<template>
  <div class="container">
    <div class="content-card">
      <h1>隱私權政策</h1>
      <p class="update-date">最後更新日期：2025年11月26日</p>

      <section>
        <h2>1. 前言</h2>
        <p>
          本隱私權政策說明「個人記帳系統」（以下簡稱「本服務」）如何收集、使用、儲存及保護您的個人資料。
          本服務為<strong>個人開發的非商業專案</strong>，旨在提供個人財務管理工具，供學習和展示用途。
        </p>
        <p>
          使用本服務即表示您同意本隱私權政策的條款。如果您不同意本政策，請勿使用本服務。
        </p>
      </section>

      <section>
        <h2>2. 服務性質聲明</h2>
        <div class="notice-box">
          <p><strong>重要聲明：</strong></p>
          <ul>
            <li>本服務為<strong>個人學習專案</strong>，非商業營運服務</li>
            <li>本服務<strong>不收取任何費用</strong></li>
            <li>本服務<strong>不販售或分享您的個人資料</strong>給第三方</li>
            <li>本服務可能隨時中止或終止，恕不另行通知</li>
            <li>開發者盡力保護您的資料安全，但<strong>不提供任何保證或擔保</strong></li>
          </ul>
        </div>
      </section>

      <section>
        <h2>3. 資料收集</h2>
        <h3>3.1 我們收集的資料</h3>
        <p>當您使用本服務時，我們可能收集以下資料：</p>
        <ul>
          <li><strong>帳號資訊：</strong>電子郵件地址（用於登入識別）</li>
          <li><strong>Google 帳號資訊：</strong>如果您選擇使用 Google 登入，我們會收集您的 Google 電子郵件地址和基本個人資料</li>
          <li><strong>財務資料：</strong>您輸入的交易記錄、帳戶資訊、預算設定等記帳資料</li>
          <li><strong>使用資訊：</strong>IP 位址、瀏覽器類型、存取時間等技術資訊（僅用於系統維護）</li>
        </ul>

        <h3>3.2 我們不收集的資料</h3>
        <ul>
          <li>真實姓名、住址、電話號碼等身份識別資訊</li>
          <li>信用卡號碼或其他金融帳戶資訊</li>
          <li>任何敏感個人資料</li>
        </ul>
      </section>

      <section>
        <h2>4. 資料使用目的</h2>
        <p>我們收集的資料僅用於以下目的：</p>
        <ul>
          <li><strong>提供服務：</strong>讓您能夠登入並使用記帳功能</li>
          <li><strong>系統維護：</strong>診斷技術問題、改善服務品質</li>
          <li><strong>安全保護：</strong>防止濫用、偵測異常活動</li>
          <li><strong>學習研究：</strong>作為個人技術學習和作品集展示</li>
        </ul>
        <p><strong>我們絕不會：</strong></p>
        <ul>
          <li>販售您的個人資料給第三方</li>
          <li>將您的資料用於廣告或行銷目的</li>
          <li>未經您同意分享您的財務資料</li>
        </ul>
      </section>

      <section>
        <h2>5. 資料儲存與安全</h2>
        <h3>5.1 資料儲存</h3>
        <ul>
          <li>所有資料儲存於加密的資料庫中</li>
          <li>密碼使用業界標準的雜湊演算法加密</li>
          <li>資料匯出檔案使用應用程式專屬密鑰加密</li>
        </ul>

        <h3>5.2 安全措施</h3>
        <ul>
          <li>使用 HTTPS 加密傳輸</li>
          <li>實施速率限制防止暴力攻擊</li>
          <li>提供雙因素認證 (2FA) 選項</li>
          <li>定期進行安全性更新</li>
        </ul>

        <h3>5.3 安全性限制</h3>
        <div class="warning-box">
          <p><strong>重要提醒：</strong></p>
          <p>
            儘管我們採取合理的安全措施，但作為個人專案，我們<strong>無法保證絕對的資料安全</strong>。
            請勿在本服務中儲存極度敏感或關鍵的財務資訊。建議定期使用資料匯出功能備份您的資料。
          </p>
        </div>
      </section>

      <section>
        <h2>6. 第三方服務</h2>
        <h3>6.1 Google OAuth 2.0</h3>
        <p>
          當您選擇使用 Google 帳號登入時，我們使用 Google OAuth 2.0 服務。Google 可能會收集您的登入資訊，
          請參閱 <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Google 隱私權政策</a>。
        </p>

        <h3>6.2 Cloudflare Turnstile</h3>
        <p>
          註冊時使用 Cloudflare Turnstile 驗證碼服務以防止濫用。Cloudflare 可能會收集您的 IP 位址和瀏覽器資訊，
          請參閱 <a href="https://www.cloudflare.com/privacypolicy/" target="_blank" rel="noopener">Cloudflare 隱私權政策</a>。
        </p>
      </section>

      <section>
        <h2>7. Cookie 和追蹤技術</h2>
        <p>本服務使用以下技術：</p>
        <ul>
          <li><strong>必要 Cookie：</strong>用於維持登入狀態和 session 管理</li>
          <li><strong>JWT Token：</strong>儲存於瀏覽器 localStorage，用於身份驗證</li>
        </ul>
        <p><strong>我們不使用：</strong></p>
        <ul>
          <li>廣告追蹤 Cookie</li>
          <li>第三方分析工具（如 Google Analytics）</li>
          <li>任何形式的使用者行為追蹤</li>
        </ul>
      </section>

      <section>
        <h2>8. 您的權利</h2>
        <p>您對自己的資料擁有以下權利：</p>
        <ul>
          <li><strong>存取權：</strong>您可以隨時查看和管理您的帳號資訊和財務資料</li>
          <li><strong>匯出權：</strong>您可以使用「資料匯出」功能下載所有資料</li>
          <li><strong>刪除權：</strong>您可以聯絡我們要求刪除您的帳號和所有相關資料</li>
          <li><strong>修正權：</strong>您可以隨時修改或刪除您的交易記錄和帳戶資訊</li>
        </ul>
        <p>
          如需行使上述權利或有任何疑問，請透過以下方式聯絡：
          <a href="mailto:hhomebase98@gmail.com">hhomebase98@gmail.com</a>
        </p>
      </section>

      <section>
        <h2>9. 資料保留</h2>
        <ul>
          <li><strong>帳號資料：</strong>保留至您刪除帳號為止</li>
          <li><strong>財務資料：</strong>保留至您主動刪除為止</li>
          <li><strong>系統日誌：</strong>保留最多 30 天用於除錯和安全監控</li>
        </ul>
        <p>
          刪除帳號後，所有資料將在 30 天內從系統中永久移除（包括備份）。
        </p>
      </section>

      <section>
        <h2>10. 兒童隱私</h2>
        <p>
          本服務不針對 13 歲以下兒童。我們不會故意收集 13 歲以下兒童的個人資料。
          如果您發現我們收集了兒童的資料，請立即聯絡我們，我們將盡快刪除相關資料。
        </p>
      </section>

      <section>
        <h2>11. 政策變更</h2>
        <p>
          我們可能不定期更新本隱私權政策。任何重大變更將透過以下方式通知您：
        </p>
        <ul>
          <li>更新本頁面頂部的「最後更新日期」</li>
          <li>在服務中顯示通知（如適用）</li>
        </ul>
        <p>
          建議您定期查看本政策以了解最新變更。繼續使用本服務即表示您接受更新後的政策。
        </p>
      </section>

      <section>
        <h2>12. 聯絡方式</h2>
        <p>如果您對本隱私權政策有任何疑問、建議或投訴，請聯絡：</p>
        <div class="contact-box">
          <p><strong>開發者：</strong>YS Hong</p>
          <p><strong>電子郵件：</strong><a href="mailto:hhomebase98@gmail.com">hhomebase98@gmail.com</a></p>
          <p><strong>專案性質：</strong>個人學習專案，非商業營運</p>
        </div>
      </section>

      <section>
        <h2>13. 免責聲明</h2>
        <div class="warning-box">
          <p><strong>重要免責聲明：</strong></p>
          <p>
            本服務為個人開發的學習專案，以「現況」提供服務，不提供任何明示或暗示的保證。
            開發者不對資料遺失、服務中斷、安全性漏洞或任何其他損害負責。
          </p>
          <p>
            使用本服務的風險由您自行承擔。我們強烈建議您定期備份重要資料，
            並避免儲存極度敏感的財務資訊。
          </p>
        </div>
      </section>

      <div class="footer-actions">
        <router-link to="/login" class="btn btn-primary">返回登入</router-link>
        <router-link to="/terms" class="btn btn-secondary">查看服務條款</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// No script needed for static content
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 40px 20px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.content-card {
  max-width: 900px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.05);
  padding: 60px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

h1 {
  color: #00d4ff;
  font-size: 2.5rem;
  margin-bottom: 10px;
  text-align: center;
}

.update-date {
  text-align: center;
  color: #a0aec0;
  font-size: 0.9rem;
  margin-bottom: 40px;
}

section {
  margin-bottom: 40px;
}

h2 {
  color: #00d4ff;
  font-size: 1.8rem;
  margin-bottom: 20px;
  margin-top: 30px;
  border-bottom: 2px solid rgba(0, 212, 255, 0.3);
  padding-bottom: 10px;
}

h3 {
  color: #4ecdc4;
  font-size: 1.3rem;
  margin-bottom: 15px;
  margin-top: 25px;
}

p {
  color: #e0e0e0;
  line-height: 1.8;
  margin-bottom: 15px;
  font-size: 1rem;
}

ul {
  color: #e0e0e0;
  line-height: 1.8;
  padding-left: 25px;
  margin-bottom: 15px;
}

li {
  margin-bottom: 10px;
}

strong {
  color: #00d4ff;
  font-weight: 600;
}

a {
  color: #00d4ff;
  text-decoration: none;
  transition: opacity 0.3s ease;
}

a:hover {
  opacity: 0.8;
  text-decoration: underline;
}

.notice-box,
.warning-box,
.contact-box {
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
}

.notice-box {
  background: rgba(0, 212, 255, 0.1);
  border-left: 4px solid #00d4ff;
}

.warning-box {
  background: rgba(255, 107, 107, 0.1);
  border-left: 4px solid #ff6b6b;
}

.contact-box {
  background: rgba(78, 205, 196, 0.1);
  border-left: 4px solid #4ecdc4;
}

.footer-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 50px;
  padding-top: 30px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn {
  padding: 12px 30px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
}

.btn-primary {
  background: linear-gradient(135deg, #00d4ff 0%, #00b4d8 100%);
  color: #1a1a2e;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}

@media (max-width: 768px) {
  .content-card {
    padding: 30px 20px;
  }

  h1 {
    font-size: 2rem;
  }

  h2 {
    font-size: 1.5rem;
  }

  h3 {
    font-size: 1.2rem;
  }

  .footer-actions {
    flex-direction: column;
  }
}
</style>
