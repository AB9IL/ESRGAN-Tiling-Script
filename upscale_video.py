import os.path
import glob
import cv2
import numpy
import torch
import RRDBNet_arch as arch
import math

model_path = 'models/RRDB_ESRGAN_x4.pth'  # models/RRDB_ESRGAN_x4.pth OR models/RRDB_PSNR_x4.pth
device = torch.device('cuda')  		# if you want to run on CPU, change 'cuda' -> cpu

inputDir = 'LR_V'					# Input directory
outputDir = 'results'				# Output directory
tileMaxSize = 200					# Size of a tile without the margin (You may lower this value if having out of memory issues)
tileMargin = 5						# Size of the margins (You may increase this value if seeing edges between tiles)
upscalingAmount = 4					# Upscaling amount of the model


def upscaleImage(model, device, img):
    # Transpose
    img = numpy.transpose(img[:, :, [2, 1, 0]], (2, 0, 1))

    imgTorch = torch.from_numpy(img).float()
    imgTorch = imgTorch.unsqueeze(0)
    imgTorch = imgTorch.to(device)
    imgNumpy = model(imgTorch).data.squeeze().float().cpu().clamp_(0, 1).numpy()

    # Re-Transpose
    return numpy.transpose(imgNumpy[[2, 1, 0], :, :], (1, 2, 0))


model = arch.RRDBNet(3, 3, 64, 23, gc=32)
model.load_state_dict(torch.load(model_path), strict=True)
model.eval()
for k, v in model.named_parameters():
    v.requires_grad = False
model = model.to(device)

print('Model path : {:s}'.format(model_path))

idx = 0
for path in glob.glob('{:s}/*'.format(inputDir)):
    idx += 1
    filename = os.path.splitext(os.path.basename(path))[0]
    print(idx, filename)
    cap = cv2.VideoCapture(path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) * 4
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) * 4
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    out = cv2.VideoWriter('{:s}/{:s}_upscaled.avi'.format(outputDir, filename), cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), fps, (width, height))
    while True:
        ret, img = cap.read()
        if img is None:
            break
        # Convert to floating point
        img = img * (1.0 / 255.0)
        # Prepare the final image
        imgOutput = numpy.zeros((img.shape[0] * upscalingAmount, img.shape[1] * upscalingAmount, 3), float)

        numTilesX = math.ceil(img.shape[0] / tileMaxSize)
        numTilesY = math.ceil(img.shape[1] / tileMaxSize)

        print('Upscaling image "{:s}" with {:d}x{:d} tiles'.format(filename, numTilesX, numTilesY))

        # For each tile in Y
        for y in range(0, numTilesY):
            tileIndexY = tileMaxSize * y
            tileIndexMaxY = min(tileIndexY + tileMaxSize, img.shape[1])
            # For each tile in X
            for x in range(0, numTilesX):
                tileIndexX = tileMaxSize * x
                tileIndexMaxX = min(tileIndexX + tileMaxSize, img.shape[0])
        		# Here we have a tile of the image x = [ tileIndexX, tileIndexMaxX ], y = [ tileIndexY, tileIndexMaxY ]
        		# Compute the available margins
                marginLeft = tileIndexX - max(tileIndexX - tileMargin, 0)
                marginTop = tileIndexY - max(tileIndexY - tileMargin, 0)
                marginRight = min(tileIndexMaxX + tileMargin, img.shape[0]) - tileIndexMaxX
                marginBottom = min(tileIndexMaxY + tileMargin, img.shape[1]) - tileIndexMaxY
        		# Create the tile using the computed size and it's margins
                imgTile = numpy.copy(img[ (tileIndexX - marginLeft):(tileIndexMaxX + marginRight), (tileIndexY - marginTop):(tileIndexMaxY + marginBottom) ])
        		# let's upscale !
                upscaledTile = upscaleImage(model, device, imgTile)
        		# Suppress the margins
                upscaledTimeNoBorder = upscaledTile[ (marginLeft * upscalingAmount):(upscaledTile.shape[0] - marginRight * upscalingAmount), (marginTop * upscalingAmount):(upscaledTile.shape[1] - marginBottom * upscalingAmount) ]
        		# Copy the tile into the final image
                imgOutput[ (tileIndexX * upscalingAmount):(tileIndexMaxX * upscalingAmount), (tileIndexY * upscalingAmount):(tileIndexMaxY * upscalingAmount) ] = upscaledTimeNoBorder

        # Convert values to [0;255]
        imgOutput = (imgOutput * 255.0).round()
        imgOutput = numpy.uint8(imgOutput)
        out.write(imgOutput)

        # Save result
    cap.release()
    out.release()
    # old output code
    # cv2.imwrite('{:s}/{:s}_upscaled.png'.format(outputDir, filename), imgOutput)
