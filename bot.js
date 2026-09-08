export default async function handler(req, res) {
  if (req.method === 'POST') {
    const update = req.body;
    
    if (update.message && update.message.text) {
      const chatId = update.message.chat.id;
      const text = update.message.text.trim();
      const token = '8744426734:AAHnITXqS8yTC-S2wOk8FSewqAiQudBwN2o';

      if (text.startsWith('/start')) {
        await sendMessage(token, chatId, "🟢 Market Bot active hai! Kisi bhi NSE stock ka naam bhejein (jaise: RELIANCE, TCS, TATAMOTORS).");
        return res.status(200).send('OK');
      }

      const symbol = text.toUpperCase();
      await sendMessage(token, chatId, `🔍 Searching ${symbol} price...`);

      try {
        // Google Finance se data fetch karna
        const response = await fetch(`https://www.google.com/finance/quote/${symbol}:NSE`);
        const html = await response.text();

        // Price aur Percentage change extract karna
        const priceMatch = html.match(/<div class="YMlKec fxKbKc">₹([0-9,.]+)<\/div>/);
        const changeMatch = html.match(/<div class="JwB6zf [^"]*">([+-]?[0-9,.]+)%<\/div>/);

        if (priceMatch && priceMatch[1]) {
          const price = priceMatch[1];
          const change = changeMatch ? changeMatch[1] : "N/A";
          const trend = change.startsWith('-') ? "🔴 Down" : "🟢 Up";

          const reply = `📊 *NSE: ${symbol}*\n💰 Price: ₹${price}\n📈 Change: ${change}%\n⚡ Trend: ${trend}`;
          await sendMessage(token, chatId, reply);
        } else {
          await sendMessage(token, chatId, `⚠️ '${symbol}' ka price data fetch nahi ho paya.`);
        }
      } catch (error) {
        await sendMessage(token, chatId, `❌ Error fetching data for ${symbol}.`);
      }
    }
    
    return res.status(200).send('OK');
  }
  
  return res.status(200).send('Node.js Telegram Bot is active!');
}

async function sendMessage(token, chatId, text) {
  await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chat_id: chatId, text: text, parse_mode: 'Markdown' })
  });
}
