// قاعدة البيانات المحلية (محاكاة)
// كل التغييرات تحفظ تلقائيًا في localStorage
const DB = {
  users: [], // قائمة المستخدمين {address, balance, age}
  miners: [], // قائمة المعدنين الحاليين (عناوين)
  minerPool: [], // مجمع المعدنيين (عناوين)
  transactions: [], // قائمة المعاملات (المنفذة)
  pendingTransactions: [], // المعاملات المعلقة
  lastUpdateNumber: 0,
};

// المستخدم الحالي (بعد استعادة الحساب)
let currentUser = null;

// حفظ البيانات في localStorage
function saveDBToLocalStorage() {
  localStorage.setItem("LibreNetworkDB", JSON.stringify(DB));
}

// تحميل البيانات من localStorage
function loadDBFromLocalStorage() {
  const data = localStorage.getItem("LibreNetworkDB");
  if (data) {
    Object.assign(DB, JSON.parse(data));
  }
}

// تحديث واجهة المستخدم الرئيسية (index.html)
function updateIndexUI() {
  document.getElementById("lastUpdateNumber").textContent = DB.lastUpdateNumber;
  document.getElementById("totalUsers").textContent = DB.users.length;
  const totalCoins = DB.users.reduce((sum, user) => sum + user.balance, 0);
  document.getElementById("totalCoins").textContent = totalCoins.toFixed(6);
  if (DB.miners.length > 0) {
    document.getElementById("lastMinerGroupId").textContent = DB.lastUpdateNumber;
    document.getElementById("lastMinerGroupCount").textContent = DB.miners.length;
  } else {
    document.getElementById("lastMinerGroupId").textContent = 0;
    document.getElementById("lastMinerGroupCount").textContent = 0;
  }
  document.getElementById("lastExecutedTxCount").textContent = DB.transactions.length;
}

// تحديث واجهة المحفظة (wallet.html)
function updateWalletUI() {
  if (currentUser) {
    document.getElementById("currentUserAddress").textContent = currentUser.address;
    document.getElementById("currentUserBalance").textContent = currentUser.balance.toFixed(6);
    document.getElementById("currentUserAge").textContent = currentUser.age || 0;
    document.getElementById("logoutButton").disabled = false;
  } else {
    document.getElementById("currentUserAddress").textContent = "غير مسجل";
    document.getElementById("currentUserBalance").textContent = "0";
    document.getElementById("currentUserAge").textContent = "0";
    document.getElementById("logoutButton").disabled = true;
  }
}

// تحديث حالة التعدين (mining.html)
function updateMiningUI() {
  const statusEl = document.getElementById("minerStatus");
  const mineBtn = document.getElementById("mineButton");
  if (!currentUser) {
    statusEl.textContent = "يرجى استعادة حساب أولاً";
    mineBtn.disabled = true;
    return;
  }
  const isMiner = DB.miners.includes(currentUser.address);
  statusEl.textContent = isMiner ? "أنت ضمن قائمة المعدنين الأخيرة" : "لست ضمن قائمة المعدنين الأخيرة";
  mineBtn.disabled = !isMiner;
}

// تحديث صفحة المعاملات (transactions.html)
function updateTransactionsUI() {
  // لا تحتاج لتحديث كثير في الواجهة هنا، لأن النماذج جاهزة.
  // لكن يمكن ربط حقول العناوين تلقائياً بالمستخدم الحالي.
  if (!currentUser) return;

  document.getElementById("changeOwnerAddress").value = "";
  document.getElementById("joinMinerAddress").value = currentUser.address;
  document.getElementById("createAccountAddress").value = "";
  document.getElementById("sendRecipient").value = "";
  document.getElementById("agePoints").value = "";
}

// تحديث صفحة قاعدة البيانات (database.html)
function updateDatabaseUI() {
  // قائمة المستخدمين
  const usersList = document.getElementById("usersList");
  usersList.innerHTML = "";
  DB.users.forEach((user) => {
    const li = document.createElement("li");
    li.textContent = `العنوان: ${user.address} - الرصيد: ${user.balance.toFixed(6)} - العمر: ${user.age || 0}`;
    usersList.appendChild(li);
  });

  // قائمة المعدنين
  const minersList = document.getElementById("minersList");
  minersList.innerHTML = "";
  DB.miners.forEach((addr) => {
    const li = document.createElement("li");
    li.textContent = addr;
    minersList.appendChild(li);
  });

  // المعاملات المنفذة
  const executedList = document.getElementById("executedTransactionsList");
  executedList.innerHTML = "";
  DB.transactions.forEach((tx, i) => {
    const li = document.createElement("li");
    li.textContent = `#${i + 1} - النوع: ${tx.type} - من: ${tx.sender || 'نظام'} - إلى: ${tx.recipient || 'N/A'} - المبلغ: ${tx.amount || 0} - الرسوم: ${tx.fee || 0}`;
    executedList.appendChild(li);
  });

  // مجمع المعدنيين
  const minerPoolList = document.getElementById("minerPoolList");
  minerPoolList.innerHTML = "";
  DB.minerPool.forEach((addr) => {
    const li = document.createElement("li");
    li.textContent = addr;
    minerPoolList.appendChild(li);
  });

  // المعاملات المعلقة
  const pendingList = document.getElementById("pendingTransactionsList");
  pendingList.innerHTML = "";
  DB.pendingTransactions.forEach((tx, i) => {
    const li = document.createElement("li");
    li.textContent = `#${i + 1} - النوع: ${tx.type} - من: ${tx.sender || 'نظام'} - إلى: ${tx.recipient || 'N/A'} - المبلغ: ${tx.amount || 0} - الرسوم: ${tx.fee || 0}`;
    pendingList.appendChild(li);
  });
}

// استعادة حساب المستخدم
function recoverAccount(event) {
  event.preventDefault();
  const pubKey = document.getElementById("recoveryPublicKey").value.trim();
  const privKey = document.getElementById("recoveryPrivateKey").value.trim();

  // تحقق بسيط للطول فقط (تعديل حسب احتياجك)
  if (pubKey.length !== 64 || privKey.length !== 64) {
    alert("المفاتيح غير صحيحة الطول!");
    return;
  }

  // ابحث عن المستخدم في DB
  const user = DB.users.find((u) => u.address === pubKey);
  if (user) {
    currentUser = user;
    alert("تم استعادة الحساب بنجاح!");
  } else {
    // إذا لم يكن موجود، أنشئ حساب جديد مؤقت (يمكن تعديل هذا السلوك)
    currentUser = { address: pubKey, balance: 0, age: 0 };
    DB.users.push(currentUser);
    saveDBToLocalStorage();
    alert("تم إنشاء حساب جديد وتم استعادته!");
  }
  updateAllUI();
}

// تسجيل خروج المستخدم
function logout() {
  currentUser = null;
  updateAllUI();
}

// إرسال معاملة إرسال مبلغ
function sendSendTransaction(event) {
  event.preventDefault();
  if (!currentUser) {
    alert("يرجى استعادة حساب أولاً");
    return;
  }
  const recipient = document.getElementById("sendRecipient").value.trim();
  const amount = parseFloat(document.getElementById("sendAmount").value);
  const fee = parseFloat(document.getElementById("sendFee").value);

  if (recipient === "" || isNaN(amount) || amount <= 0) {
    alert("الرجاء إدخال بيانات صحيحة");
    return;
  }

  if (currentUser.balance < amount + fee) {
    alert("الرصيد غير كافٍ لإجراء هذه المعاملة");
    return;
  }

  // خصم المبلغ والرسوم من المرسل
  currentUser.balance -= amount + fee;

  // اضافة للمستلم (إذا موجود)
  let recipientUser = DB.users.find((u) => u.address === recipient);
  if (!recipientUser) {
    // أنشئ حساب جديد للمستلم
    recipientUser = { address: recipient, balance: 0, age: 0 };
    DB.users.push(recipientUser);
  }
  recipientUser.balance += amount;

  // إضافة المعاملة إلى قائمة المعاملات المعلقة
  const tx = {
    type: "إرسال مبلغ",
    sender: currentUser.address,
    recipient,
    amount,
    fee,
    timestamp: Date.now(),
  };
  DB.pendingTransactions.push(tx);

  saveDBToLocalStorage();
  updateAllUI();
  alert("تم إرسال المعاملة وسيتم تنفيذها لاحقاً");
}

// إرسال معاملة تزويد العمر التعدينى
function sendAgeTransaction(event) {
  event.preventDefault();
  if (!currentUser) {
    alert("يرجى استعادة حساب أولاً");
    return;
  }
  const points = parseInt(document.getElementById("agePoints").value);
  const fee = parseFloat(document.getElementById("ageFee").value);

  if (isNaN(points) || points <= 0) {
    alert("الرجاء إدخال نقاط صحيحة");
    return;
  }
  if (currentUser.balance < fee) {
    alert("الرصيد غير كافٍ لدفع الرسوم");
    return;
  }

  currentUser.balance -= fee;
  currentUser.age = (currentUser.age || 0) + points;

  const tx = {
    type: "تزويد العمر التعدينى",
    sender: currentUser.address,
    amount: points,
    fee,
    timestamp: Date.now(),
  };
  DB.pendingTransactions.push(tx);

  saveDBToLocalStorage();
  updateAllUI();
  alert("تم إرسال معاملة تزويد العمر التعدينى");
}

// إرسال معاملة إنشاء حساب جديد
function sendCreateAccountTransaction(event) {
  event.preventDefault();
  if (!currentUser) {
    alert("يرجى استعادة حساب أولاً");
    return;
  }
  const newAddress = document.getElementById("createAccountAddress").value.trim();
  const fee = parseFloat(document.getElementById("createFee").value);

  if (newAddress === "") {
    alert("يرجى إدخال عنوان الحساب الجديد");
    return;
  }

  if (DB.users.find((u) => u.address === newAddress)) {
    alert("هذا العنوان موجود مسبقاً");
    return;
  }

  if (currentUser.balance < fee) {
    alert("الرصيد غير كافٍ لدفع الرسوم");
    return;
  }

  currentUser.balance -= fee;

  const newUser = { address: newAddress, balance: 0, age: 0 };
  DB.users.push(newUser);

  const tx = {
    type: "إنشاء حساب",
    sender: currentUser.address,
    recipient: newAddress,
    fee,
    timestamp: Date.now(),
  };
  DB.pendingTransactions.push(tx);

  saveDBToLocalStorage();
  updateAllUI();
  alert("تم إرسال معاملة إنشاء الحساب الجديد");
}

// إرسال معاملة تغيير الملكية
function sendChangeOwnerTransaction(event) {
  event.preventDefault();
  if (!currentUser) {
    alert("يرجى استعادة حساب أولاً");
    return;
  }
  const newOwner = document.getElementById("changeOwnerAddress").value.trim();
  const fee = parseFloat(document.getElementById("changeOwnerFee").value);

  if (newOwner === "") {
    alert("يرجى إدخال عنوان المستخدم الجديد");
    return;
  }

  if (currentUser.balance < fee) {
    alert("الرصيد غير كافٍ لدفع الرسوم");
    return;
  }

  // تنفيذ التغيير (تغيير عنوان الحساب الحالي)
  // ملاحظة: في النظام الحقيقي يحتاج تحقق أكثر
  currentUser.balance -= fee;
  const oldAddress = currentUser.address;
  currentUser.address = newOwner;

  // تحديث في قاعدة البيانات (استبدال العنوان)
  const userIndex = DB.users.findIndex((u) => u.address === oldAddress);
  if (userIndex !== -1) {
    DB.users[userIndex].address = newOwner;
  }

  const tx = {
    type: "تغيير الملكية",
    sender: oldAddress,
    recipient: newOwner,
    fee,
    timestamp: Date.now(),
  };
  DB.pendingTransactions.push(tx);

  saveDBToLocalStorage();
  updateAllUI();
  alert("تم إرسال معاملة تغيير الملكية");
}

// إرسال معاملة دخول مجمع المعدنين
function sendJoinMinerPoolTransaction(event) {
  event.preventDefault();
  if (!currentUser) {
    alert("يرجى استعادة حساب أولاً");
    return;
  }
  const fee = parseFloat(document.getElementById("joinMinerFee").value);

  if (currentUser.balance < fee) {
    alert("الرصيد غير كافٍ لدفع الرسوم");
    return;
  }

  if (!DB.minerPool.includes(currentUser.address)) {
    DB.minerPool.push(currentUser.address);
  }

  currentUser.balance -= fee;

  const tx = {
    type: "دخول مجمع المعدنين",
    sender: currentUser.address,
    fee,
    timestamp: Date.now(),
  };
  DB.pendingTransactions.push(tx);

  saveDBToLocalStorage();
  updateAllUI();
  alert("تم إرسال معاملة دخول مجمع المعدنين");
}

// تنفيذ المعاملات المعلقة (محاكاة تنفيذ وتحديث القوائم)
function executePendingTransactions() {
  if (DB.pendingTransactions.length === 0) return;

  DB.pendingTransactions.forEach((tx) => {
    // مثال بسيط: إضافة المعاملات إلى المنفذة
    DB.transactions.push(tx);

    // حسب نوع المعاملة يمكن تنفيذ تأثيرات إضافية (مثلاً تحديث القوائم)
  });
  DB.pendingTransactions = [];
  DB.lastUpdateNumber++;

  // تحديث قائمة المعدنين (مثال: تحديث حسب مجمع المعدنين)
  DB.miners = [...DB.minerPool];

  saveDBToLocalStorage();
  updateAllUI();
  alert("تم تنفيذ جميع المعاملات المعلقة وتحديث الشبكة");
}

// زر التعدين
document.addEventListener("DOMContentLoaded", () => {
  loadDBFromLocalStorage();
  updateAllUI();

  const logoutBtn = document.getElementById("logoutButton");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", logout);
  }

  const mineBtn = document.getElementById("mineButton");
  if (mineBtn) {
    mineBtn.addEventListener("click", () => {
      executePendingTransactions();
    });
  }
});

// تحديث جميع واجهات المستخدم المفتوحة
function updateAllUI() {
  updateIndexUI();
  updateWalletUI();
  updateMiningUI();
  updateTransactionsUI();
  updateDatabaseUI();
}
