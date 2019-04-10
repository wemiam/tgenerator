import tensorflow as tf
import numpy as np
import os, argparse, time, random
from model import BiLSTM_CRF
from utils import str2bool, get_logger, get_entity
from data import read_corpus, read_dictionary, tag2label, random_embedding


## Session configuration
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # default: 0
config = tf.ConfigProto()
config.gpu_options.allow_growth = True
config.gpu_options.per_process_gpu_memory_fraction = 0.2  # need ~700MB GPU memory


## hyperparameters
parser = argparse.ArgumentParser(description='BiLSTM-CRF for Chinese NER task')
parser.add_argument('--train_data', type=str, default='data_path', help='train data source')
parser.add_argument('--test_data', type=str, default='data_path', help='test data source')
parser.add_argument('--batch_size', type=int, default=64, help='#sample of each minibatch')
parser.add_argument('--epoch', type=int, default=40, help='#epoch of training')
parser.add_argument('--hidden_dim', type=int, default=300, help='#dim of hidden state')
parser.add_argument('--optimizer', type=str, default='Adam', help='Adam/Adadelta/Adagrad/RMSProp/Momentum/SGD')
parser.add_argument('--CRF', type=str2bool, default=True, help='use CRF at the top layer. if False, use Softmax')
parser.add_argument('--lr', type=float, default=0.001, help='learning rate')
parser.add_argument('--clip', type=float, default=5.0, help='gradient clipping')
parser.add_argument('--dropout', type=float, default=0.5, help='dropout keep_prob')
parser.add_argument('--update_embedding', type=str2bool, default=True, help='update embedding during training')
parser.add_argument('--pretrain_embedding', type=str, default='random', help='use pretrained char embedding or init it randomly')
parser.add_argument('--embedding_dim', type=int, default=300, help='random init char embedding_dim')
parser.add_argument('--shuffle', type=str2bool, default=True, help='shuffle training data before each epoch')
parser.add_argument('--mode', type=str, default='demo', help='train/test/demo')
parser.add_argument('--demo_model', type=str, default='1521112368', help='model for test and demo')
args = parser.parse_args()


## get char embeddings
word2id = read_dictionary(os.path.join('.', args.train_data, 'word2id.pkl'))
if args.pretrain_embedding == 'random':
    embeddings = random_embedding(word2id, args.embedding_dim)
else:
    embedding_path = 'pretrain_embedding.npy'
    embeddings = np.array(np.load(embedding_path), dtype='float32')


## read corpus and get training data
if args.mode != 'demo':
    train_path = os.path.join('.', args.train_data, 'train_data')
    test_path = os.path.join('.', args.test_data, 'test_data')
    train_data = read_corpus(train_path)
    test_data = read_corpus(test_path); test_size = len(test_data)


## paths setting
paths = {}
timestamp = str(int(time.time())) if args.mode == 'train' else args.demo_model
output_path = os.path.join('.', args.train_data+"_save", timestamp)
if not os.path.exists(output_path): os.makedirs(output_path)
summary_path = os.path.join(output_path, "summaries")
paths['summary_path'] = summary_path
if not os.path.exists(summary_path): os.makedirs(summary_path)
model_path = os.path.join(output_path, "checkpoints/")
if not os.path.exists(model_path): os.makedirs(model_path)
ckpt_prefix = os.path.join(model_path, "model")
paths['model_path'] = ckpt_prefix
result_path = os.path.join(output_path, "results")
paths['result_path'] = result_path
if not os.path.exists(result_path): os.makedirs(result_path)
log_path = os.path.join(result_path, "log.txt")
paths['log_path'] = log_path
get_logger(log_path).info(str(args))





def evaluate_words(lines):
    print("start evaluate_words")
    ckpt_file = tf.train.latest_checkpoint(model_path)
    print(ckpt_file)
    paths['model_path'] = ckpt_file
    model = BiLSTM_CRF(args, embeddings, tag2label, word2id, paths, config=config)
    model.build_graph()
    saver = tf.train.Saver()
    with tf.Session(config=config) as sess:
        print('============= demo =============')
        saver.restore(sess, ckpt_file)

        demo_sent = lines
        print(demo_sent)
        demo_sent = list(demo_sent.strip())
        print(demo_sent)
        demo_data = [(demo_sent, ['O'] * len(demo_sent))]
        tag = model.demo_one(sess, demo_data)
        PER, LOC, ORG = get_entity(tag, demo_sent)
        print('PER: {}\nLOC: {}\nORG: {}'.format(PER, LOC, ORG))

if __name__ == "__main__":

    #evaluate_words("安倍晋三感谢习近平主席对日本遭受台风、地震灾害表达的慰问。安倍表示，日本长期以来致力于参与中国改革开放进程，中国的发展也为日本带来积极和重要影响。当前日中关系正回到正常轨道，双方合作空间进一步扩大。日本希望同中国建立更加紧密的关系，实现共同发展繁荣。日方愿作出积极努力，同中方加强高层交往，争取更多合作成果，加快推进日中关系改善和发展。为此，日方愿努力增进两国民间友好，妥善处理好敏感问题。在历史和台湾问题上，日方坚持在两国政治文件中确认的立场，这一点没有任何变化。日方重视中国在国际和地区事务中的重要作用，希望就事关地区和平稳定的重大问题同中方加强沟通和协调。")evaluate_words("安倍晋三感谢习近平主席对日本遭受台风、地震灾害表达的慰问。安倍表示，日本长期以来致力于参与中国改革开放进程，中国的发展也为日本带来积极和重要影响。当前日中关系正回到正常轨道，双方合作空间进一步扩大。日本希望同中国建立更加紧密的关系，实现共同发展繁荣。日方愿作出积极努力，同中方加强高层交往，争取更多合作成果，加快推进日中关系改善和发展。为此，日方愿努力增进两国民间友好，妥善处理好敏感问题。在历史和台湾问题上，日方坚持在两国政治文件中确认的立场，这一点没有任何变化。日方重视中国在国际和地区事务中的重要作用，希望就事关地区和平稳定的重大问题同中方加强沟通和协调。")
    evaluate_words("安倍晋三感谢习近平主席对日本遭受台风、地震灾害表达的慰问。安倍表示，日本长期以来致力于参与中国改革开放进程，中国的发展也为日本带来积极和重要影响。当前日中关系正回到正常轨道，双方合作空间进一步扩大。日本希望同中国建立更加紧密的关系，实现共同发展繁荣。日方愿作出积极努力，同中方加强高层交往，争取更多合作成果，加快推进日中关系改善和发展。为此，日方愿努力增进两国民间友好，妥善处理好敏感问题。在历史和台湾问题上，日方坚持在两国政治文件中确认的立场，这一点没有任何变化。日方重视中国在国际和地区事务中的重要作用，希望就事关地区和平稳定的重大问题同中方加强沟通和协调。丁薛祥、杨洁篪、王毅、何立峰等参加会见。")