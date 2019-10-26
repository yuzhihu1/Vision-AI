import torch
import argparse
from mvordata import *
from unet_mvor import *
from resnet34 import *
import cv2
import pickle
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import time

def main(args):
        device = ["cpu", "cuda"][torch.cuda.is_available()]
        model_path = args.model
        models = [Unet_Mvor(), Unet_Resnet34()]
        model = models[int(args.model_type)]
        model.load_state_dict(torch.load(model_path))
        model.to(device)
        model.eval()
        path = args.test_path
        JsonFile = "../../mvor-master/annotations/camma_mvor_2018.json"
        with torch.no_grad():
                with open(path, 'rb') as f:
                        test_path = pickle.load(f)
                        print(test_path[0])
                        test_data = Mvordata(JsonFile, test_path)
                        test_data_list, test_label_list = test_data.to_dataset()
                        n = 0
                        acc = 0
                        for i in tqdm.tqdm(range(len(test_data_list)), desc='Calculating IoU'):
                                x = test_data_list[i]
                                x = torch.tensor(x).float().view(1, 3, 480, 640)
                                y = test_label_list[i]
                                y = torch.tensor(y).float()
                                x = x.to(device)
                                y = y.to(device)
                                xh = model(x)
                                xh = xh[0]
                                xh = xh.permute(1, 2, 0)
                                xh1 = xh[:, :, 1]
                                xh0 = xh[:, :, 0]
                                xh_box = xh1 > xh0
                                intersection = xh_box.float() * y
                                intersection_sum = intersection.sum()
                                union_sum = xh_box.sum() + y.sum() - intersection_sum
                                if intersection_sum > 0:
                                        n += 1
                                        acc += intersection_sum / union_sum
                        print(n, acc/n)

                # image_path = test_path[i+99]
                # print(image_path)
                # data = cv2.imread(image_path[0], cv2.IMREAD_UNCHANGED)
                # data = np.transpose(data, (2, 0, 1))
                # data = torch.tensor(data).float().view(1, 3, 480, 640)
                # start_time = time.time()
                # xh = model(data)
                # print("--- %s seconds ---" % (time.time() - start_time))
                # xh = xh[0]
                # xh = xh.permute(1, 2, 0)
                # xh1 = xh[:, :, 1]
                # xh0 = xh[:, :, 0]
                # xh_box = xh1 > xh0
                # if args.evaluate:
                #       print(xh_box.size())
                        #
                # f = plt.figure()
                # f.add_subplot(1,2, 1)
                # imgplot = mpimg.imread(image_path[0])
                # plt.imshow(imgplot)
                # f.add_subplot(1,2, 2)
                # plt.imshow(xh_box)
                # plt.show(block=True)


if __name__ == '__main__':
        parser = argparse.ArgumentParser()
        parser.add_argument("--model_type")
        parser.add_argument("--model")
        parser.add_argument("--test_path")
        args = parser.parse_args()
        main(args)
        