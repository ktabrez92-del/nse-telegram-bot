export default async function handler(req, res) {
  if (req.method === 'POST') {
    const update = req.body;
    
    if (update.message && update.message.text) {
      const chatId = update.message.chat.id;
      const text = update.message.text.trim();

      const token = '8744426734:AAHnITXqS8yTC-S2wOk8FSewqAiQudBwN2o';
      const replyText = `Aapne stock search kiya: ${text}. Live data fetch ho raha hai!`;

      await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: chatId, text: replyText })
      });
    }
    
    return res.status(200).send('OK');
  }
  
  return res.status(200).send('Node.js Telegram Bot is active!');
}
