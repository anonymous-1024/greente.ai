import tensorflow as tf
import smtag as sag
import config
class PGNAgent(object):    #object??
    def __init__(self,n_input,n_actions):
        self.nx=n_input
        self.h1=4*self.nx
        self.h2=4*n_actions
        self.ny=n_actions
        self.learning_rate=config.learning_rate
        
        self.x=tf.placeholder(tf.float32, [None,self.nx], name="input_x")
        self.W1=tf.get_variable("w1",shape=[self.nx,self.h1],initializer=tf.contrib.layers.xavier_initializer())
        self.layer1=tf.nn.relu(tf.matmul(self.x,self.W1))
        self.W2=tf.get_variable("w2",shape=[self.h1,self.h2],initializer=tf.contrib.layers.xavier_initializer())
        self.layer2=tf.nn.relu(tf.matmul(self.layer1,self.W2))
        self.W3=tf.get_variable("w3",shape=[self.h2,self.ny],initializer=tf.contrib.layers.xavier_initializer())
        self.action_logits=tf.matmul(self.layer2,self.W3)
        self.sample_action=tf.multinomial(self.action_logits, 1)
        self.tvars=tf.trainable_variables()
        self.y=tf.placeholder(tf.int32,(None,1),name="input_y")
        self.advantages = tf.placeholder(tf.float32,name="reward_signal")
        
        self.loss=tf.reduce_mean(self.advantages*tf.nn.sparse_softmax_cross_entropy_with_logits(logits=[self.action_logits],labels=self.y))
        self.grads=tf.gradients(self.loss,self.tvars)
        self.optimizer = tf.train.AdamOptimizer(learning_rate=self.learning_rate)
        self.W1Grad = tf.placeholder(tf.float32,name="batch_grad1") # Placeholders to send the final gradients through when we update.
        self.W2Grad = tf.placeholder(tf.float32,name="batch_grad2")
        self.W3Grad = tf.placeholder(tf.float32,name="batch_grad3")
        self.batchGrad = [self.W1Grad,self.W2Grad,self.W3Grad]
        self.updateGrads = self.optimizer.apply_gradients(zip(self.batchGrad,self.tvars))
        
        init=tf.global_variables_initializer()
        self.sess=tf.Session()
        self.sess.run(init)
    def rollaction(self,obs):
        action=self.sess.run(self.sample_action,feed_dict={self.x:obs})
        return action
    def calGrad(self,epx,epy,epr):
        epgrads=self.sess.run(self.grads,feed_dict={self.x:epx,self.y:epy,self.advantages:epr})
        return epgrads
    def applyGrad(self,gradBuffer):
        self.sess.run(self.updateGrads,feed_dict={self.W1Grad:gradBuffer[0],self.W2Grad:gradBuffer[1],self.W3Grad:gradBuffer[2]})

        
        
        
        
        