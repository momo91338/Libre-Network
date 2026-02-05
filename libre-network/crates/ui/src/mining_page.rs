use eframe::egui::{Ui, Button, Label};
use node::node::LibreNode;
use tokio::sync::Mutex;
use std::sync::Arc;

pub struct MiningPage {
    pub node: Option<Arc<Mutex<LibreNode>>>,
    mining_active: bool,
}

impl MiningPage {
    pub fn show(&mut self, ui: &mut Ui) {
        ui.heading("Mining Page");

        if self.node.is_none() {
            ui.label("Node is not started yet. Please start the node.");
            return;
        }

        if ui.button(if self.mining_active { "Stop Mining" } else { "Start Mining" }).clicked() {
            self.mining_active = !self.mining_active;

            if let Some(node_arc) = &self.node {
                let node = node_arc.clone();
                let active = self.mining_active;
                tokio::spawn(async move {
                    if active {
                        // start mining (مثال بسيط)
                        node.lock().await.miner_manager.mine_update().await;
                    } else {
                        // stop mining logic
                    }
                });
            }
        }

        ui.label(format!("Mining is {}", if self.mining_active { "Active" } else { "Inactive" }));
    }
}

impl Default for MiningPage {
    fn default() -> Self {
        Self {
            node: None,
            mining_active: false,
        }
    }
}
