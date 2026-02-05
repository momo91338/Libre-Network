use eframe::egui::{Ui};

pub struct SettingsPage {}

impl SettingsPage {
    pub fn show(&mut self, ui: &mut Ui) {
        ui.heading("Settings and Terms");
        ui.label("شروط الاستخدام، إعدادات التطبيق...");
    }
}

impl Default for SettingsPage {
    fn default() -> Self {
        Self {}
    }
}
