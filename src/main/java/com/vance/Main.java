package com.vance;

import com.vance.Camera;
import nu.pattern.OpenCV;

public class Main {
    public static void main( String[] args ) {
        OpenCV.loadLocally();
        Camera camera = new Camera();
        camera.startCamera();
    }
}
