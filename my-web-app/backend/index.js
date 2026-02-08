// backend/index.js
const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const accountsRouter = require('./routes/accounts')
const updatesRouter = require('./routes/updates');
const minersRouter = require('./routes/miners');
const transactionsRouter = require('./routes/transactions');

const connectDB = require('./db');

const app = express();
const PORT = process.env.PORT || 4000;

// اتصال بقاعدة البيانات MongoDB
connectDB();

// إعدادات وسط التنفيذ
app.use(cors());
app.use(express.json());

// ربط الراوترز
app.use('/api/updates', updatesRouter);
app.use('/api/miners', minersRouter);
app.use('/api/transactions', transactionsRouter);
app.use('/api/accounts', accountsRouter)
// اختبار الاتصال
app.get('/', (req, res) => {
  res.send('Libre Network Backend API is running');
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
