#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <time.h>
#include <pthread.h>
#include <mysql.h>
#include <uuid/uuid.h>
#include <stdarg.h>

/*
This is an INT packet parser, it can parse INT packet to integer or string and save it to database
*/

// byte
#define headerSize 22
#define fieldNum 8
#define srHeaderSize 64
#define idPayloadSize 4

int write_log(FILE *pFile, const char *format, ...);

void doBinTrans(char message[], int startPos, int size, char binstr[]);
void doBin2Str(char binarr[], char binstr[], int binLength);
void doPayloadBin2Str(char binarr[], char binstr[], int binLength);
long doBin2Int(char binarr[], int startPos, int endPos);
void doFormatStr(char binstr[], char formattedStrArr[][fieldNum * fieldNum]);
void doFormatInt(char binarr[], long formattedIntArr[fieldNum]);
static int callback(void *NotUsed, int argc, char **argv, char **azColName);
void mysqlConnection(const char *host, const char *user, const char *password, const char *database);

int write_log(FILE *pFile, const char *format, ...)
{
    va_list arg;
    int done;

    va_start(arg, format);
    //done = vfprintf (stdout, format, arg);

    time_t time_log = time(NULL);
    struct tm *tm_log = localtime(&time_log);
    fprintf(pFile, "\n%04d-%02d-%02d %02d:%02d:%02d ", tm_log->tm_year + 1900, tm_log->tm_mon + 1, tm_log->tm_mday, tm_log->tm_hour, tm_log->tm_min, tm_log->tm_sec);

    done = vfprintf(pFile, format, arg);
    va_end(arg);

    fflush(pFile);
    return done;
}

MYSQL conn;

void mysqlConnection(const char *host, const char *user, const char *password, const char *database)
{
    mysql_init(&conn);

    my_bool my_true=1;

    mysql_options(&conn,MYSQL_OPT_RECONNECT, &my_true);

    if (mysql_real_connect(&conn, host, user, password, database, 0, NULL, 0))
    {
        printf("Connection success!\n");
    }
    else
    {
        fprintf(stderr, "Connection failed!\n");
        if (mysql_errno(&conn))
        {
            fprintf(stderr, "Connection error %d: %s\n", mysql_errno(&conn), mysql_error(&conn));
        }
        exit(EXIT_FAILURE);
    }
}

int main(int argc, char **argv)
{
    char *host_id = argv[1];
    printf("host_id is %s\n", host_id);
    char file_name[50] = {"./packet/logs/receiveLog"};
    FILE *log_file = fopen(strcat(strcat(file_name, host_id), ".log"), "a");
    if (!log_file)
    {
        FILE *log_file = fopen(strcat(strcat(file_name, host_id), ".log"), "w");
    }
    write_log(log_file, "int receiver opened, id is %s", host_id);
    int port = 2222;
    char *zErrMsg = 0;
    int rc;
    char sql[256];

    int sin_len;
    char message[65535];
    int socket_descriptor;
    struct sockaddr_in sin;

    mysqlConnection("localhost", "root", "fnl", "fnl");
    // mysqlConnection("192.168.147.1", "root", "root", "fnl");

    printf("waiting for packet \n");
    bzero(&sin, sizeof(sin));
    sin.sin_family = AF_INET;
    sin.sin_addr.s_addr = inet_addr("0.0.0.0");
    sin.sin_port = htons(port);
    sin_len = sizeof(sin);
    socket_descriptor = socket(AF_INET, SOCK_DGRAM, 0);
    bind(socket_descriptor, (struct sockaddr *)&sin, sizeof(sin));

    time_t timep;
    uuid_t uuid;
    char packetId[36];

    while (1)
    {
        time(&timep);
        srand((unsigned)timep);
        uuid_generate(uuid);
        uuid_unparse(uuid, packetId);

        // printf("time %d ,packetId %s \n", (int)timep, packetId);

        memset(message, 0, sizeof(message));
        int rsize = recvfrom(socket_descriptor, message, sizeof(message), 0, (struct sockaddr *)&sin, &sin_len);
        printf("received %d byte data \n", rsize);

        int headerNum = (rsize - srHeaderSize - idPayloadSize) / headerSize;
        char binarr[headerSize * fieldNum];
        char binstr[headerSize * fieldNum + 1];
        char formattedStrArr[fieldNum][fieldNum * fieldNum];
        long formattedIntArr[fieldNum * 8];

        char binPayLoadArr[idPayloadSize * 8];
        int payloadStartPos = headerSize * headerNum + srHeaderSize;
        // printf("payloadStartPos %d, idpayloadSize %d \n", payloadStartPos, idPayloadSize);
        doBinTrans(message, payloadStartPos, idPayloadSize, binPayLoadArr);
        long payLoadInt = doBin2Int(binPayLoadArr, 0, idPayloadSize * 8 - 1);

        write_log(log_file, "received a packet, action id is %ld", payLoadInt);

        int i;
        // printf("header num %d\n", headerNum);
        for (i = 0; i < headerNum; i++)
        {
            // printf("header no:%d \n", i);
            binstr[0] = '\0';
            doBinTrans(message, i * headerSize + srHeaderSize, headerSize, binarr);
            // doBin2Str(binarr, binstr, headerSize * fieldNum);
            // doFormatStr(binstr, formattedStrArr);
            doFormatInt(binarr, formattedIntArr);

            sprintf(sql,
                    "insert into `fnl_int` (`device_no`,`ingress_port`,`egress_port`,`ingress_global_timestamp`,`enq_timestamp`,`enq_qdepth`,`deq_timedelta`,`deq_qdepth`,`udp_port`,`timestamp`,`packet_id`,`action_id`) values (%ld,%ld,%ld,%ld,%ld,%ld,%ld,%ld,%d,%d,'%s',%ld);",
                    formattedIntArr[0], formattedIntArr[1], formattedIntArr[2], formattedIntArr[3], formattedIntArr[4], formattedIntArr[5], formattedIntArr[6], formattedIntArr[7],
                    port, (int)timep, packetId, payLoadInt);
            // printf("%s\n", sql);
            int res = mysql_query(&conn, sql);
            if (!res)
            {
                printf("Inserted %lu rows actId %ld\n", (unsigned long)mysql_affected_rows(&conn), payLoadInt);
            }
            else
            {
                fprintf(stderr, "Insert error %d: %s\n", mysql_errno(&conn), mysql_error(&conn));
            }
            // fprintf(stdout, "record inserted \n");
        }
    }
    exit(0);
    return (EXIT_SUCCESS);
}

void doBinTrans(char message[], int startPos, int size, char binarr[])
{
    // printf("start pos :%d \n", startPos);
    int i;
    int m = 0;
    for (i = startPos; i < size + startPos; i++)
    {
        // printf("\ni=%d\n", i);
        char j, k;
        for (j = 7; j >= 0; j--)
        {
            // printf("\nj=%d  ", j);
            k = message[i] >> j;
            binarr[m] = k & 1;
            // printf("%d", binarr[m]);
            m++;
        }
        // printf("\n");
    }
}

void doBin2Str(char binarr[], char binstr[], int binLength)
{
    char st[2];
    int i;
    for (i = 0; i < binLength; i++)
    {
        // printf("%d", binarr[i]);
        sprintf(st, "%d", binarr[i]);
        strcat(binstr, st);
    }
    // printf("\n");
    // printf("str: %s \n",binstr);
}

void doPayloadBin2Str(char binarr[], char binstr[], int binLength)
{
    char st[2];
    int i;
    for (i = 0; i < binLength; i++)
    {
        // printf("%d", binarr[i]);
        sprintf(st, "%d", binarr[i]);
        // printf("speintf st is %s \n", st);
        strcat(binstr, st);
        // printf("strcat binstr is %s\n", binstr);
    }
    binstr[binLength] = '\0';
    // printf("\n");
    // printf("str: %s \n",binstr);
}

long doBin2Int(char binarr[], int startPos, int endPos)
{
    int i;
    long binInt = 0;
    long binExp = 1;
    for (i = endPos; i >= startPos; i--)
    {
        binInt += binarr[i] * binExp;
        binExp *= 2;
    }
    // printf("\nbinint %ld\n", binInt);
    return binInt;
}

void doFormatStr(char binstr[], char formattedStrArr[][fieldNum * fieldNum])
{
    // printf("str: %s \n", binstr);
    int hdrLen[] = {8, 9, 9, 48, 32, 19, 32, 19};
    char tmpFormat[fieldNum * fieldNum];
    int position = 0;
    int i;
    for (i = 0; i < fieldNum; i++)
    {
        int j;
        for (j = 0; j < hdrLen[i]; j++)
        {
            tmpFormat[j] = binstr[position + j];
        }
        tmpFormat[j] = '\0';
        position += hdrLen[i];
        strcpy(formattedStrArr[i], tmpFormat);
        // printf("str %s j=%d\n", formattedStrArr[i], j);
    }
}
void doFormatInt(char binarr[], long formattedIntArr[fieldNum])
{
    int hdrLen[] = {8, 9, 9, 48, 32, 19, 32, 19};
    int i;
    int position = 0;
    for (i = 0; i < fieldNum; i++)
    {
        formattedIntArr[i] = doBin2Int(binarr, position, position + hdrLen[i] - 1);
        position += hdrLen[i];
        // printf("\nformatted int position %d hdrLen %d  %d => %ld\n", position, hdrLen[i], i, formattedIntArr[i]);
    }
}