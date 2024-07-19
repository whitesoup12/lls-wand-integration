module com.vance.wand {
    requires javafx.controls;
    requires javafx.fxml;

    requires opencv;
    requires java.desktop;
    requires javafx.swing;

    opens com.vance.wand to javafx.fxml;
    exports com.vance.wand;
}