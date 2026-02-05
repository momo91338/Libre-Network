use eframe::egui;
use ui::app::LibreApp;

fn main() -> Result<(), eframe::Error> {
    let options = eframe::NativeOptions::default();
    eframe::run_native(
        "Libre Network UI",
        options,
        Box::new(|_cc| Box::new(LibreApp::default())),
    )
}
