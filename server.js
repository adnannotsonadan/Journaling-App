import express from 'express';
import session from 'express-session';
import dotenv from 'dotenv';
import authRoutes from './routes/authRoutes.js';
import journalRoutes from './routes/journalRoutes.js';


dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

app.use(session({
  secret: 'keyboard_cat',
  resave: false,
  saveUninitialized: false
}));

app.use('/auth', authRoutes);
app.use('/journal', journalRoutes);

app.use(express.static('public')); // serve static files

// Redirect root to register page to start
app.get('/', (req, res) => {
  res.sendFile('register.html', { root: './public' });
});

// Serve login page explicitly if needed
app.get('/login', (req, res) => {
  res.sendFile('login.html', { root: './public' });
});

// Serve journal page only if logged in, else redirect to login
app.get('/journal', (req, res) => {
  if (req.session.user) {
    res.sendFile('journal.html', { root: './public' });  // your journal page
  } else {
    res.redirect('/login');
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
});
