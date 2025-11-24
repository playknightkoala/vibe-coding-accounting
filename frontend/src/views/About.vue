<template>
  <div class="about-container">
    <div class="about-content">
      <h1>關於本專案</h1>
      
      <section class="section">
        <h2>📊 專案簡介</h2>
        <p>
          這是一個功能完整的<strong>個人記帳與預算管理系統</strong>，旨在幫助使用者有效管理個人財務、追蹤支出、設定預算目標，並透過視覺化報表深入了解財務狀況。
        </p>
        <p>
          本專案是個人全端開發作品，展示了現代 Web 應用程式開發的完整流程，從前端介面設計到後端 API 開發，再到資料庫設計與部署。
        </p>
      </section>

      <section class="section">
        <h2>✨ 主要功能</h2>
        <ul>
          <li><strong>多幣別支援</strong>：支援 TWD、USD、JPY 等多種貨幣，並提供即時匯率轉換</li>
          <li><strong>交易管理</strong>：快速記帳、交易分類、描述自動完成（支援拼音搜尋）</li>
          <li><strong>預算追蹤</strong>：設定月度/日度預算，即時追蹤預算使用狀況</li>
          <li><strong>報表分析</strong>：多維度財務報表，包含類別分析、帳戶分析、排名統計等</li>
          <li><strong>帳戶管理</strong>：支援現金、銀行、信用卡、儲值卡等多種帳戶類型</li>
          <li><strong>安全性</strong>：使用者認證、JWT Token、2FA 雙因素驗證</li>
        </ul>
      </section>

      <section class="section">
        <h2>🛠️ 技術堆疊</h2>
        <div class="tech-stack">
          <div class="tech-category">
            <h3>前端</h3>
            <ul>
              <li>Vue 3 (Composition API)</li>
              <li>TypeScript</li>
              <li>Pinia (狀態管理)</li>
              <li>Vue Router</li>
              <li>Axios</li>
            </ul>
          </div>
          <div class="tech-category">
            <h3>後端</h3>
            <ul>
              <li>Python FastAPI</li>
              <li>SQLAlchemy (ORM)</li>
              <li>PostgreSQL</li>
              <li>JWT Authentication</li>
              <li>APScheduler (排程任務)</li>
            </ul>
          </div>
          <div class="tech-category">
            <h3>部署</h3>
            <ul>
              <li>Docker & Docker Compose</li>
              <li>Nginx (反向代理)</li>
              <li>SSL/TLS (HTTPS)</li>
            </ul>
          </div>
        </div>
      </section>

      <section class="section">
        <h2>👨‍💻 開發者</h2>
        <p>
          <strong>YS Hong</strong> - 全端工程師
        </p>
        <p>
          這個專案是我的個人作品集之一，展示了我在全端開發、系統架構設計、以及現代 Web 技術應用方面的能力。
        </p>
      </section>

      <section class="section">
        <h2>📝 使用說明</h2>
        <p>
          本系統為個人專案展示用途，如需試用請<router-link to="/register">註冊帳號</router-link>或使用測試帳號登入。
        </p>
        <p>
          所有資料僅供展示使用，請勿輸入真實的財務資訊。
        </p>
      </section>

      <section class="section">
        <h2>🔗 相關連結</h2>
        <ul>
          <li><router-link to="/login">登入系統</router-link></li>
          <li><router-link to="/register">註冊帳號</router-link></li>
        </ul>
      </section>

      <div class="footer-note">
        <p>© 2025 YS Hong. 本專案為個人作品，僅供展示與學習用途。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// No special logic needed for static about page
</script>

<style scoped>
.about-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 40px 20px;
}

.about-content {
  max-width: 900px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

h1 {
  color: #00d4ff;
  font-size: 2.5rem;
  margin-bottom: 30px;
  text-align: center;
}

.section {
  margin-bottom: 40px;
}

.section h2 {
  color: #00d4ff;
  font-size: 1.8rem;
  margin-bottom: 15px;
  border-bottom: 2px solid rgba(0, 212, 255, 0.3);
  padding-bottom: 10px;
}

.section h3 {
  color: #4ecdc4;
  font-size: 1.3rem;
  margin-bottom: 10px;
}

.section p {
  color: #e0e0e0;
  line-height: 1.8;
  margin-bottom: 15px;
}

.section ul {
  color: #e0e0e0;
  line-height: 1.8;
  padding-left: 20px;
}

.section li {
  margin-bottom: 10px;
}

.section strong {
  color: #00d4ff;
}

.tech-stack {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.tech-category {
  background: rgba(0, 212, 255, 0.05);
  padding: 20px;
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.tech-category ul {
  padding-left: 20px;
}

.footer-note {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
  color: #a0a0a0;
  font-size: 0.9rem;
}

a, .section a {
  color: #00d4ff;
  text-decoration: none;
  transition: color 0.3s ease;
}

a:hover, .section a:hover {
  color: #4ecdc4;
  text-decoration: underline;
}

@media (max-width: 768px) {
  .about-content {
    padding: 20px;
  }

  h1 {
    font-size: 2rem;
  }

  .section h2 {
    font-size: 1.5rem;
  }

  .tech-stack {
    grid-template-columns: 1fr;
  }
}
</style>
