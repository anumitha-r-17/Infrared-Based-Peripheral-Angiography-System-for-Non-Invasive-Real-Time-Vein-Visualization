# Infrared-Based-Peripheral-Angiography-System-for-Non-Invasive-Real-Time-Vein-Visualization
A non-invasive, real-time vein visualization system using Near-Infrared (NIR) imaging and image processing techniques such as CLAHE and Gaussian filtering to enhance subcutaneous vein detection. Designed as a portable, low-cost solution for IV cannulation and vascular assessment across diverse skin tones.
100% Standalone Edge Execution: The entire camera capture, image processing, and web streaming pipeline run on a single Raspberry Pi 5 node.
Real-time Local Processing: Captures video frames using a background thread and processes them with minimal latency using optimized local computer vision techniques.
CLAHE Enhancement: Employs Contrast Limited Adaptive Histogram Equalization (CLAHE) to boost regional image contrast, making hidden vein structures clearly visible against surrounding skin.
Web-Based Viewer Interface: Serves a lightweight multi-part JPEG video stream accessible by any smartphone, tablet, or monitor connected to the same local network.
