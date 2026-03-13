const express = require('express');
const fs = require('fs');
const app = express();
app.use(express.json());
app.use(express.static('public')); // Unga HTML files inga irukkanum

const DATA_FILE = './data.json';

// 1. Get Q&A
app.get('/get-qa', (req, res) => {
    const data = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
    res.json(data);
});

// 2. Admin Update Q&A
app.post('/update-qa', (req, res) => {
    const { question, answer } = req.body;
    let data = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
    
    // Pudhu data-vah add pannu
    data.push({ q: question.toLowerCase(), a: answer });
    
    // File-la save pannu
    fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
    res.json({ message: "Update Success!" });
});

app.listen(3000, () => console.log("Server running on port 3000"));
