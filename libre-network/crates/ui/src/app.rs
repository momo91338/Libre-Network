use eframe::egui::{Context, CentralPanel, TopBottomPanel};
use crate::{wallet_page::WalletPage, mining_page::MiningPage, network_status_page::NetworkStatusPage, settings_page::SettingsPage};

use wallet::keys::Wallet;
use node::node::LibreNode;
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::runtime::Runtime;

#[derive(Default)]
pub struct LibreApp {
    current_page: Page,
    wallet_page: WalletPage,
    mining_page: MiningPage,
    network_status_page: NetworkStatusPage,
    settings_page: SettingsPage,

    // المحفظة (يمكن تكون None في البداية)
    pub wallet: Option<Wallet>,

    // العقدة: ملف node في async + Arc + Mutex
    pub node: Option<Arc<Mutex<LibreNode>>>,

    // Tokio runtime لتشغيل async من sync (واجهة)
    rt: Runtime,
}

#[derive(PartialEq)]
enum Page {
    Wallet,
    Mining,
    NetworkStatus,
    Settings,
}

impl Default for Page {
    fn default() -> Self {
        Page::Wallet
    }
}

impl LibreApp {
    pub fn new() -> Self {
        Self {
            current_page: Page::Wallet,
            wallet_page: WalletPage::default(),
            mining_page: MiningPage::default(),
            network_status_page: NetworkStatusPage::default(),
            settings_page: SettingsPage::default(),
            wallet: None,
            node: None,
            rt: Runtime::new().expect("Failed to create Tokio Runtime"),
        }
    }

    // إنشاء محفظة جديدة (async مع تنفيذ من sync)
    pub fn create_wallet(&mut self) {
        let wallet = self.rt.block_on(async { Wallet::new().await });
        self.wallet = Some(wallet);
        self.wallet_page.wallet = self.wallet.clone();
    }

    // بدء العقدة node بشكل async
    pub fn start_node(&mut self) {
        let node = self.rt.block_on(async { LibreNode::new().await });
        self.node = Some(Arc::new(Mutex::new(node)));
        self.mining_page.node = self.node.clone();
        self.network_status_page.node = self.node.clone();
        self.wallet_page.node = self.node.clone();
    }
}

impl eframe::App for LibreApp {
    fn update(&mut self, ctx: &Context, _frame: &mut eframe::Frame) {
        TopBottomPanel::top("top_panel").show(ctx, |ui| {
            ui.horizontal(|ui| {
                if ui.button("Wallet").clicked() {
                    self.current_page = Page::Wallet;
                }
                if ui.button("Mining").clicked() {
                    self.current_page = Page::Mining;
                }
                if ui.button("Network Status").clicked() {
                    self.current_page = Page::NetworkStatus;
                }
                if ui.button("Settings").clicked() {
                    self.current_page = Page::Settings;
                }
                // أزرار تشغيل العقدة وإنشاء المحفظة
                if ui.button("Start Node").clicked() {
                    self.start_node();
                }
                if ui.button("Create Wallet").clicked() {
                    self.create_wallet();
                }
            });
        });

        CentralPanel::default().show(ctx, |ui| {
            match self.current_page {
                Page::Wallet => self.wallet_page.show(ui),
                Page::Mining => self.mining_page.show(ui),
                Page::NetworkStatus => self.network_status_page.show(ui),
                Page::Settings => self.settings_page.show(ui),
            }
        });
    }
}
