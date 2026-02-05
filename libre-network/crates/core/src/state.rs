use crate::{user::User, miner::Miner, update::Update};
use std::collections::HashMap;

/// تمثل الحالة العامة للشبكة، تشمل المستخدمين، قائمة المعدنين، وقائمة التحديثات الحالية.
pub struct GlobalState {
    /// خريطة المستخدمين حيث المفتاح هو مصفوفة بايت 32 (مثل عنوان أو معرف المستخدم).
    pub users: HashMap<[u8; 32], User>,

    /// قائمة عناوين المعدنين النشطين في النظام.
    pub miner_pool: Vec<[u8; 32]>,

    /// قائمة بقوائم المعدنين، كل قائمة تمثل مجموعة معدنين معينة.
    pub miner_lists: Vec<Vec<Miner>>,

    /// التحديث الحالي إن وجد.
    pub current_update: Option<Update>,
}

/// تمثل حالة البلوكشين، مثل ارتفاع السلسلة (عدد الكتل).
#[derive(Clone, Debug)]
pub struct State {
    /// ارتفاع السلسلة أو عدد الكتل الحالية.
    pub height: u64,
}

impl State {
    /// تنشئ حالة جديدة مع ارتفاع سلسلة يساوي صفر.
    pub fn new() -> Self {
        State { height: 0 }
    }
}

impl GlobalState {
    /// تنشئ حالة عامة جديدة فارغة.
    pub fn new() -> Self {
        Self {
            users: HashMap::new(),
            miner_pool: Vec::new(),
            miner_lists: Vec::new(),
            current_update: None,
        }
    }
}
