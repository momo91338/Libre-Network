use eframe::egui::{Ui};
use node::node::LibreNode;
use tokio::sync::Mutex;
use std::sync::Arc;

pub struct NetworkStatusPage {
    pub node: Option<Arc<Mutex<LibreNode>>>,
}

impl NetworkStatusPage {
    pub fn show(&mut self, ui: &mut Ui) {
        ui.heading("Network Status");

        if let Some(node_arc) = &self.node {
            let node = node_arc.clone();
            // للوصول للبيانات async نحتاج spawn (أو استراتيجيات تحديث)
            // هنا مثال بسيط يعرض رقم التحديث الحالي:
            // (يُفضل استخدام قنوات تحديث state فعلية لتحديث الواجهة بشكل تلقائي)
            tokio::spawn(async move {
                let update_id = node.lock().await.state.current_update_id();
                println!("Current Update ID: {}", update_id);
            });

            ui.label("Check console for current update (async example)");
        } else {
            ui.label("Node not started yet");
        }
    }
}

impl Default for NetworkStatusPage {
    fn default() -> Self {
        Self { node: None }
    }
}
