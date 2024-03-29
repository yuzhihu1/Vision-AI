import argparse

import torch
import tqdm

import vision_ai

import unet_cifar10
import visualize_cifar10_unet

def main(args):
    device = ["cpu", "cuda"][torch.cuda.is_available()]

    dataloader, testloader = vision_ai.data.cifar10_cover.get(
        root="~/torchvision-data",
        download=True,
        batch_size=args.batch_size,
        num_workers=args.workers,
        box=args.box,
        shuffle_test=True
    )

    cpu_model = unet_cifar10.Unet()
    model = torch.nn.DataParallel(cpu_model).to(device)
    lossf = torch.nn.MSELoss(reduction="sum")
    optim = torch.optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=args.l2_reg
    )

    sched = torch.optim.lr_scheduler.CosineAnnealingLR(
        optim, T_max=args.epochs
    )

    for epoch in range(1, args.epochs+1):

        model.train()

        avg = vision_ai.utils.MovingAvg(decay=0.95)
        with tqdm.tqdm(dataloader, ncols=80) as bar:
            for xr, xc, y in bar:
                xr = xr.to(device)
                xc = xc.to(device)
                xh = model(xc)
                n = len(xr)
                loss = lossf(xh.view(n, -1), xr.view(n, -1))/n

                optim.zero_grad()
                loss.backward()
                optim.step()

                avg.update(loss.item())
                bar.set_description("Loss: %.4f" % avg.peek())

        sched.step()

        model.eval()

        save_cycle = (epoch >= args.save_cycle and not epoch % args.save_cycle)

        acc = n = 0.0
        visualized = False
        with torch.no_grad():
            for xr, xc, y in testloader:
                xr = xr.to(device)
                xc = xc.to(device)
                xh = model(xc)
                
                if save_cycle and not visualized:
                    visualized = True
                    visualize_cifar10_unet.visualize(
                        xr, xh, xc, args.save_images
                    )
                
                b = len(xr)
                acc += lossf(xh.view(b, -1), xr.view(b, -1)).item()
                n += b

        print("Epoch %d test L2-loss: %.2f" % (epoch, acc/n))

        if save_cycle:
            save_model(cpu_model, args.save)
    
    save_model(cpu_model, args.save)


def save_model(model, save_path):
    print("Saving model to %s..." % save_path)
    torch.save(model.state_dict(), save_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    
    # System parameters
    parser.add_argument("--batch_size", type=int, required=True)
    parser.add_argument("--workers", type=int, required=True)
    
    # Training cycle parameters
    parser.add_argument("--epochs", type=int, required=True)
    parser.add_argument("--lr", type=float, required=True)
    parser.add_argument("--l2_reg", type=float, required=True)
    parser.add_argument("--box", type=int, required=True)
    
    # Committing to disk
    parser.add_argument("--save", required=True)
    parser.add_argument("--save_cycle", type=int, required=True)
    parser.add_argument("--save_images", type=int, default=10)
    
    args = parser.parse_args()
    main(args)
