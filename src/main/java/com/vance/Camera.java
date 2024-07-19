package com.vance;

import org.opencv.core.*;
import org.opencv.core.Point;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.imgproc.Imgproc;
import org.opencv.utils.Converters;
import org.opencv.videoio.VideoCapture;
import org.opencv.videoio.VideoWriter;
import org.opencv.videoio.Videoio;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.awt.image.DataBuffer;
import java.awt.image.DataBufferByte;
import java.awt.image.DataBufferInt;
import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.BiFunction;

public class Camera {
    private VideoCapture videoCapture = new VideoCapture();
    private ScheduledExecutorService timer;

    private static final Double HUE_START = 100.0;
    private static final Double HUE_STOP = 130.0;
    private static final Double SATURATION_START = 0.0;
    private static final Double SATURATION_STOP = 255.0;
    private static final Double VALUE_START = 88.45;
    private static final Double VALUE_STOP = 255.0;

    private List<Point> lista = new ArrayList<>();

    public void startCamera() {
        this.videoCapture.open(0);

        if(this.videoCapture.isOpened()) {
            System.out.println("Capturing");

            this.captureXFramesToVideo();
        }
    }

    private void captureXFramesToVideo() {
        VideoWriter videoWriter = new VideoWriter(
                "D:/Development/wand3/vid.avi",
                VideoWriter.fourcc('M','J','P','G'), 30,
                new Size(videoCapture.get(Videoio.CAP_PROP_FRAME_WIDTH),
                        videoCapture.get(Videoio.CAP_PROP_FRAME_HEIGHT)));
        try {
            int frameNumber = 0;
            while(frameNumber < 30) {
                Mat frame = grabFrame(frameNumber);
                videoWriter.write(frame);
                frameNumber++;
                Thread.sleep(33);
            }
            System.out.println("Releasing");
            videoCapture.release();
            videoWriter.release();

            for(Point point: lista) {
                System.out.println(point);
            }
        }catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void runVideo() {
        Runnable frameGrabber = new Runnable() {
            @Override
            public void run()
            {
                Mat frame = grabFrame(0);
            }
        };

        this.timer = Executors.newSingleThreadScheduledExecutor();
        this.timer.scheduleAtFixedRate(frameGrabber, 0, 33, TimeUnit.MILLISECONDS);
    }

    private Mat grabFrame(int frameNumber) {
        Mat frame = new Mat();
        try {
            this.videoCapture.read(frame);
            if(!frame.empty()) {
                // init
                Mat blurredImage = new Mat();
                Mat hsvImage = new Mat();
                Mat mask = new Mat();
                Mat morphOutput = new Mat();

                Imgproc.blur(frame, blurredImage, new Size(7, 7));

                Imgproc.cvtColor(blurredImage, hsvImage, Imgproc.COLOR_BGR2HSV);

                // remember: H ranges 0-180, S and V range 0-255
                Scalar minValues = new Scalar(HUE_START, SATURATION_START, VALUE_START);
                Scalar maxValues = new Scalar(HUE_STOP, SATURATION_STOP, VALUE_STOP);

                Core.inRange(hsvImage, minValues, maxValues, mask);

                // morphological operators
                // dilate with large element, erode with small ones
                Mat dilateElement = Imgproc.getStructuringElement(Imgproc.MORPH_RECT, new Size(24, 24));
                Mat erodeElement = Imgproc.getStructuringElement(Imgproc.MORPH_RECT, new Size(12, 12));

                Imgproc.erode(mask, morphOutput, erodeElement);
                Imgproc.erode(morphOutput, morphOutput, erodeElement);

                Imgproc.dilate(morphOutput, morphOutput, dilateElement);
                Imgproc.dilate(morphOutput, morphOutput, dilateElement);

                this.saveImage(morphOutput, String.valueOf(frameNumber));

                this.findAndDraw(morphOutput, frame);

                return frame;
            }
        }catch (Exception e) {
            System.err.print("Exception during the image elaboration...");
            e.printStackTrace();
        }
        return frame;
    }

    private Mat findAndDraw(Mat maskedImage, Mat frame) {
        // init
        List<MatOfPoint> contours = new ArrayList<>();
        Mat hierarchy = new Mat();

        // find contours
        Imgproc.findContours(maskedImage, contours, hierarchy, Imgproc.RETR_CCOMP, Imgproc.CHAIN_APPROX_SIMPLE);

        if(!contours.isEmpty()) {

            for (MatOfPoint contour : contours) {
                for( Point p: contour.toList()) {
                    Point point = new Point(p.x, p.y);
                    lista.add(point);
                }
            }
        }

        // if any contour exist...
        if (hierarchy.size().height > 0 && hierarchy.size().width > 0) {
            // for each contour, display it in blue
            for (int idx = 0; idx >= 0; idx = (int) hierarchy.get(0, idx)[0]) {
                Imgproc.drawContours(frame, contours, idx, new Scalar(250, 0, 0));
            }
        }

        return frame;
    }

    private void saveImage(Mat original, String filename) {
        // init
        BufferedImage image = null;
        int width = original.width(), height = original.height(), channels = original.channels();
        byte[] sourcePixels = new byte[width * height * channels];
        original.get(0, 0, sourcePixels);

        if (original.channels() > 1)
        {
            image = new BufferedImage(width, height, BufferedImage.TYPE_3BYTE_BGR);
        }
        else
        {
            image = new BufferedImage(width, height, BufferedImage.TYPE_BYTE_GRAY);
        }
        final byte[] targetPixels = ((DataBufferByte) image.getRaster().getDataBuffer()).getData();
        System.arraycopy(sourcePixels, 0, targetPixels, 0, sourcePixels.length);

        try {
            File outputfile = new File("D:/Development/wand3/images/" + filename + ".png");
            ImageIO.write(image, "png", outputfile);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}