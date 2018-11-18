import pymysql

class DBParser():
    """
    Intereavtive with database, transfer function to SQL and get the result
    """

    def __init__(self, switchSum, sqlInfo, switchesInfo):
        """
        Initialize the database connection information and truncate the database

        :param switchSum: the number of switches
        :param sqlInfo: the database link info
        """
        self.switchSum = switchSum
        self.sqlInfo = sqlInfo
        self.switchesInfo = switchesInfo
        self.traunce_db()

    def traunce_db(self):
        self.searchDB('truncate `fnl_int`')

    def searchDB(self, sql):
        """
        Link to database and search database with SQL

        :param sql: SQL senence
        :returns: the result dict
        """
        def doConn():
            conn = pymysql.connect(host=self.sqlInfo['host'],
                                   user=self.sqlInfo['user'],
                                   passwd=self.sqlInfo['passwd'],
                                   db=self.sqlInfo['db'],
                                   port=self.sqlInfo['port'],
                                   charset=self.sqlInfo['charset'])
            return conn
        try:
            self.conn = doConn()
        except:
            self.conn = doConn()
        cursor = self.conn.cursor()
        cursor.execute(sql)
        values = cursor.fetchall()
        cursor.close()
        self.conn.close()
        return values

    def parser(self, actionID):
        """
        Find the record by action id

        after got the raw result by SQL query, the program will calculate the meam queue depth for each link in all results

        :param actionID: action id given by controller
        :returns: rewatrd matrix which contains queue depth of each link
        """
        rewardMatr = [[[]
                       for i in range(self.switchSum)] for i in range(self.switchSum)]
        # sql = "select id,device_no,enq_qdepth,deq_qdepth,packet_id from fnl.fnl_int where action_id=" + \
        #     str(actionID)
        sql = "select device_no,egress_port,deq_timedelta,enq_qdepth from fnl.fnl_int where action_id=" + \
            str(actionID)
        values = self.searchDB(sql)
        print('db value len ', len(values))

        # # append the queue_depth of every link to the reward_matrix
        # for i in range(len(values) - 1):
        #     if values[i][4] == values[i + 1][4]:
        #         downswitch = values[i + 1][1]
        #         upswitch = values[i][1]
        #         depth = values[i][2] + values[i + 1][3]
        #         rewardMatr[downswitch][upswitch].append(depth)
        # # calculate the average of queue_depth
        # for i in range(self.switchSum):
        #     for j in range(self.switchSum):
        #         if len(rewardMatr[i][j]):
        #             avg = sum(rewardMatr[i][j]) / \
        #                 len(rewardMatr[i][j])
        #             rewardMatr[i][j] = avg
        #         else:
        #             rewardMatr[i][j] = 0

        # append the queue_time_delta of every link to the reward_matrix
        for value in values:
            device_no = int(value[0])
            egress_port = int(value[1])
            deq_timedelta = int(value[2])
            enq_qdepth=int(value[3])
            next_device_no = int(
                self.switchesInfo[device_no].ports[egress_port - 1].deviceName[1:])
            rewardMatr[device_no][next_device_no].append(deq_timedelta/100)
            # rewardMatr[device_no][next_device_no].append(enq_qdepth)
        # calculate the average of queue_depth
        for i in range(self.switchSum):
            for j in range(self.switchSum):
                if len(rewardMatr[i][j]):
                    avg = sum(rewardMatr[i][j]) / \
                        len(rewardMatr[i][j])
                    rewardMatr[i][j] = avg
                else:
                    rewardMatr[i][j] = 0

        print('rewardMatr ', rewardMatr)
        return rewardMatr

    def __del__(self):
        # self.conn.close()
        pass


if __name__ == '__main__':
    pass
    # switchSum = 6
    # actionID = 1
    # dbInfo = {
    #     'host': '192.168.150.1',
    #     # 'host': 'localhost',
    #     'user': 'root',
    #     # 'passwd': 'fnl',
    #     'passwd': 'root',
    #     'db': 'fnl',
    #     'port': 3306,
    #     'charset': 'utf8'
    # }
    # dbp = DBParser(switchSum, dbInfo)
    # import time
    # dbp.parser(actionID)
    # time.sleep(10)
    # dbp.parser(actionID)
    # time.sleep(10)
    # dbp.parser(actionID)
    # time.sleep(10)
    # dbp.parser(actionID)
    # time.sleep(10)
    # dbp.parser(actionID)
    # time.sleep(10)
    # dbp.parser(actionID)
    # time.sleep(10)
    # dbp.parser(actionID)
