# TEED learned photo-edge preparation

Source: https://github.com/xavysp/TEED

Pinned revision: `40fa4b1391dc6424f88989d0ca75d5b592c8681d`.
Checkpoint: `checkpoints/BIPED/5/5_model.pth`, the checkpoint selected by the upstream `main.py` default. The unmodified 249,139-byte checkpoint is retained. The original MIT license, architecture, dataset preprocessing, Smish function and README are included as `upstream-*` files.

Paper: Xavier Soria, Yachuan Li, Mohammad Rouhani and Angel D. Sappa, *Tiny and Efficient Model for the Edge Detection Generalization*, ICCV Workshops 2023. https://openaccess.thecvf.com/content/ICCV2023W/RCV/html/Soria_Tiny_and_Efficient_Model_for_the_Edge_Detection_Generalization_ICCVW_2023_paper.html

`weights.bin` contains all 36 checkpoint tensors as lossless little-endian float32 (235,640 bytes). Source Conv2d kernels are transposed OIHW→HWIO; ConvTranspose2d kernels IOHW→HWOI. Depthwise grouped kernels are reshaped to TensorFlow's HWIM ordering. `model.json` records shapes, offsets, sizes and SHA256 hashes of the source checkpoint and every packaged source/weight file.

Packaging read PyTorch's zip checkpoint using an allowlisted pickle reader supporting only OrderedDict, FloatStorage descriptors and `_rebuild_tensor_v2`. It did not import or execute PyTorch code, run inference or produce artwork. No weights were quantized, trained, selected against the user's subjects or changed.

`photo-edges.ts` implements the official three-block TED network, all three upsampling heads, DoubleFusion depthwise fusion and Smish activation in TensorFlow.js. Explicit symmetric PyTorch padding is retained before stride-2 convolutions/maxpool because TensorFlow SAME padding would shift their sampling. Input is BGR float32 centered by upstream `BIPED_mean[:3]` = [103.939,116.779,123.68]. Output is the fused sigmoid probability map, normalized to black edges on white, resized back to the original crop size. Internal inference defaults to a longest side of 512 and dimensions divisible by eight. It is a learned source guide, not native-text artwork and not the separate AAHub-credited manga extractor.

All inference occurs locally when a genuine app control calls `photoEdges`; no source photo is sent to a service. The guide may still contain texture or miss weak contours. Inspect it beside the photograph before retaining a trace. Model provenance and correct execution do not establish the best portrait result or an optimal choice for every face.
