<template>
  <div class="container">
    <div class="content-card">
      <h1>服務條款</h1>
      <p class="update-date">最後更新日期：2025年11月26日</p>

      <section>
        <h2>1. 服務性質與接受條款</h2>
        <p>
          歡迎使用「個人記帳系統」（以下簡稱「本服務」）。本服務由 YS Hong（以下簡稱「開發者」或「我們」）
          開發和維護，為<strong>個人學習專案</strong>，旨在提供個人財務管理工具供學習和展示用途。
        </p>
        <p>
          使用本服務即表示您已閱讀、理解並同意受本服務條款（以下簡稱「本條款」）的約束。
          如果您不同意本條款的任何部分，請勿使用本服務。
        </p>

        <div class="notice-box">
          <p><strong>重要聲明：</strong></p>
          <ul>
            <li>本服務為<strong>個人非商業專案</strong></li>
            <li>本服務<strong>完全免費</strong>，不收取任何費用</li>
            <li>本服務可能隨時變更、暫停或終止，恕不另行通知</li>
            <li>本服務<strong>不提供任何保證或擔保</strong></li>
          </ul>
        </div>
      </section>

      <section>
        <h2>2. 使用資格</h2>
        <p>使用本服務，您必須：</p>
        <ul>
          <li>年滿 13 歲</li>
          <li>具有完全行為能力</li>
          <li>遵守所有適用的法律和法規</li>
          <li>提供真實、準確的電子郵件地址</li>
        </ul>
        <p>
          未滿 18 歲的使用者應在家長或監護人同意下使用本服務。
        </p>
      </section>

      <section>
        <h2>3. 帳號註冊與安全</h2>
        <h3>3.1 帳號建立</h3>
        <ul>
          <li>您可以透過電子郵件註冊或使用 Google 帳號登入</li>
          <li>您必須提供有效的電子郵件地址</li>
          <li>每個電子郵件地址僅能註冊一個帳號</li>
        </ul>

        <h3>3.2 帳號安全</h3>
        <ul>
          <li>您有責任保護您的帳號密碼和登入憑證</li>
          <li>建議啟用雙因素認證 (2FA) 以增加安全性</li>
          <li>您應對帳號下的所有活動負責</li>
          <li>如發現未經授權的帳號使用，請立即聯絡我們</li>
        </ul>

        <h3>3.3 帳號終止</h3>
        <p>您可以隨時刪除您的帳號。我們也保留以下權利：</p>
        <ul>
          <li>暫停或終止違反本條款的帳號</li>
          <li>因技術或安全原因暫停或終止任何帳號</li>
          <li>因服務終止而刪除所有帳號</li>
        </ul>
      </section>

      <section>
        <h2>4. 服務使用規範</h2>
        <h3>4.1 允許的使用</h3>
        <p>本服務僅供以下合法用途：</p>
        <ul>
          <li>個人財務記帳和預算管理</li>
          <li>追蹤個人收支和帳戶餘額</li>
          <li>產生個人財務報表</li>
          <li>備份和匯出個人財務資料</li>
        </ul>

        <h3>4.2 禁止的使用</h3>
        <p>使用本服務時，您不得：</p>
        <ul>
          <li>用於任何非法目的或違反法律的活動</li>
          <li>嘗試未經授權存取系統或其他使用者的資料</li>
          <li>干擾、破壞或損害服務的運作</li>
          <li>使用自動化工具（如機器人）濫用服務</li>
          <li>上傳惡意軟體、病毒或有害程式碼</li>
          <li>進行逆向工程、反編譯或試圖取得原始碼</li>
          <li>冒充他人或虛假陳述您與他人的關係</li>
          <li>侵犯他人的知識產權或隱私權</li>
        </ul>
      </section>

      <section>
        <h2>5. 資料與隱私</h2>
        <h3>5.1 您的資料</h3>
        <ul>
          <li>您輸入的所有財務資料（交易、帳戶、預算）歸您所有</li>
          <li>您可以隨時匯出或刪除您的資料</li>
          <li>我們不會將您的資料用於商業目的或分享給第三方</li>
        </ul>

        <h3>5.2 隱私保護</h3>
        <p>
          我們重視您的隱私。有關資料收集、使用和保護的詳細資訊，
          請參閱我們的<router-link to="/privacy">隱私權政策</router-link>。
        </p>

        <h3>5.3 資料備份</h3>
        <div class="warning-box">
          <p><strong>重要提醒：</strong></p>
          <p>
            儘管我們會盡力保護您的資料，但作為個人專案，<strong>我們無法保證資料的永久保存</strong>。
            我們強烈建議您：
          </p>
          <ul>
            <li>定期使用「資料匯出」功能備份您的資料</li>
            <li>將備份檔案儲存在安全的位置</li>
            <li>避免依賴本服務作為唯一的財務記錄來源</li>
          </ul>
        </div>
      </section>

      <section>
        <h2>6. 智慧財產權</h2>
        <h3>6.1 服務內容</h3>
        <p>
          本服務的所有內容，包括但不限於：
        </p>
        <ul>
          <li>軟體程式碼、設計、介面</li>
          <li>文字、圖形、標誌</li>
          <li>功能和特性</li>
        </ul>
        <p>
          均為開發者的財產，受著作權法和其他智慧財產權法律保護。
        </p>

        <h3>6.2 有限授權</h3>
        <p>
          我們授予您有限的、非獨家的、不可轉讓的、可撤銷的授權，
          允許您存取和使用本服務供個人非商業用途。
        </p>

        <h3>6.3 開源專案</h3>
        <p>
          本專案作為學習和展示用途，部分程式碼可能在未來以開源形式發布。
          具體授權條款將在開源時另行說明。
        </p>
      </section>

      <section>
        <h2>7. 服務可用性</h2>
        <h3>7.1 服務水準</h3>
        <p>本服務以「現況」（AS IS）提供，我們：</p>
        <ul>
          <li><strong>不保證</strong>服務的持續可用性或不中斷</li>
          <li><strong>不保證</strong>所有功能的正常運作</li>
          <li><strong>不保證</strong>錯誤或缺陷會被修復</li>
          <li><strong>不保證</strong>服務的安全性或資料完整性</li>
        </ul>

        <h3>7.2 服務變更</h3>
        <p>我們保留以下權利，恕不另行通知：</p>
        <ul>
          <li>修改、暫停或終止服務的任何功能</li>
          <li>變更服務的介面、設計或架構</li>
          <li>限制某些功能的使用或存取</li>
        </ul>

        <h3>7.3 服務終止</h3>
        <p>
          我們可能因任何原因（包括但不限於維護成本、技術限制、時間限制）
          永久終止本服務。如可能，我們會提前 30 天通知，讓您有時間匯出資料。
        </p>
      </section>

      <section>
        <h2>8. 第三方服務</h2>
        <p>本服務整合以下第三方服務：</p>
        <ul>
          <li><strong>Google OAuth 2.0：</strong>用於 Google 帳號登入</li>
          <li><strong>Cloudflare Turnstile：</strong>用於註冊驗證</li>
        </ul>
        <p>
          使用這些第三方服務受其各自的服務條款和隱私權政策約束：
        </p>
        <ul>
          <li><a href="https://policies.google.com/terms" target="_blank" rel="noopener">Google 服務條款</a></li>
          <li><a href="https://www.cloudflare.com/website-terms/" target="_blank" rel="noopener">Cloudflare 服務條款</a></li>
        </ul>
      </section>

      <section>
        <h2>9. 免責聲明</h2>
        <div class="warning-box">
          <h3>9.1 一般免責聲明</h3>
          <p>
            本服務為個人學習專案，以「現況」和「現有」基礎提供，
            <strong>不提供任何明示或暗示的保證</strong>，包括但不限於：
          </p>
          <ul>
            <li>適銷性保證</li>
            <li>特定用途適用性保證</li>
            <li>不侵權保證</li>
            <li>資料準確性或完整性保證</li>
          </ul>

          <h3>9.2 財務建議免責</h3>
          <p>
            本服務<strong>不提供任何財務建議</strong>。本服務僅為記帳工具，
            不應被視為專業財務諮詢、投資建議或稅務建議。
            如需專業建議，請諮詢合格的財務顧問。
          </p>

          <h3>9.3 資料遺失免責</h3>
          <p>
            開發者對於任何資料遺失、損壞或無法存取<strong>不承擔任何責任</strong>。
            您有責任定期備份您的資料。
          </p>
        </div>
      </section>

      <section>
        <h2>10. 責任限制</h2>
        <div class="warning-box">
          <p>
            在法律允許的最大範圍內，開發者對於因使用或無法使用本服務而產生的任何損害
            <strong>不承擔任何責任</strong>，包括但不限於：
          </p>
          <ul>
            <li>直接、間接、附帶、特殊或後果性損害</li>
            <li>利潤損失、資料遺失或業務中斷</li>
            <li>因依賴本服務資料而做出的財務決策</li>
            <li>第三方服務故障或安全漏洞</li>
            <li>未經授權的帳號存取</li>
          </ul>
          <p>
            <strong>使用本服務的所有風險由您自行承擔。</strong>
          </p>
        </div>
      </section>

      <section>
        <h2>11. 賠償</h2>
        <p>
          您同意賠償、保護並使開發者免受因以下原因產生的任何索賠、損失、責任、費用和開支：
        </p>
        <ul>
          <li>您違反本條款</li>
          <li>您違反任何法律或第三方權利</li>
          <li>您使用本服務的方式</li>
          <li>您上傳或提交的任何內容</li>
        </ul>
      </section>

      <section>
        <h2>12. 條款變更</h2>
        <p>
          我們保留隨時修改本條款的權利。重大變更將透過以下方式通知：
        </p>
        <ul>
          <li>更新本頁面頂部的「最後更新日期」</li>
          <li>在服務中顯示通知（如適用）</li>
          <li>透過電子郵件通知（重大變更）</li>
        </ul>
        <p>
          變更生效後繼續使用本服務即表示您接受修改後的條款。
          如果您不同意新條款，請停止使用本服務並刪除您的帳號。
        </p>
      </section>

      <section>
        <h2>13. 爭議解決</h2>
        <h3>13.1 準據法</h3>
        <p>
          本條款受中華民國法律管轄並依其解釋，不考慮法律衝突原則。
        </p>

        <h3>13.2 管轄權</h3>
        <p>
          因本條款產生的任何爭議應提交中華民國有管轄權的法院解決。
        </p>

        <h3>13.3 友好協商</h3>
        <p>
          在提起訴訟之前，我們鼓勵雙方嘗試透過友好協商解決爭議。
          如有任何問題或糾紛，請先聯絡：<a href="mailto:hhomebase98@gmail.com">hhomebase98@gmail.com</a>
        </p>
      </section>

      <section>
        <h2>14. 一般條款</h2>
        <h3>14.1 完整協議</h3>
        <p>
          本條款與隱私權政策構成您與開發者之間關於本服務的完整協議，
          取代所有先前的口頭或書面協議。
        </p>

        <h3>14.2 可分割性</h3>
        <p>
          如本條款的任何條文被認定為無效或不可執行，
          該條文應在可能的最小範圍內被修改，其餘條文仍具完全效力。
        </p>

        <h3>14.3 不放棄權利</h3>
        <p>
          開發者未行使或延遲行使本條款下的任何權利，不構成對該權利的放棄。
        </p>

        <h3>14.4 不可轉讓</h3>
        <p>
          您不得轉讓本條款下的權利或義務。開發者可以自由轉讓本條款下的權利和義務。
        </p>
      </section>

      <section>
        <h2>15. 聯絡資訊</h2>
        <p>如果您對本服務條款有任何疑問或需要協助，請聯絡：</p>
        <div class="contact-box">
          <p><strong>開發者：</strong>YS Hong</p>
          <p><strong>電子郵件：</strong><a href="mailto:hhomebase98@gmail.com">hhomebase98@gmail.com</a></p>
          <p><strong>專案類型：</strong>個人學習專案（非商業營運）</p>
          <p><strong>回應時間：</strong>盡力而為，不保證即時回應</p>
        </div>
      </section>

      <section>
        <h2>16. 致謝與感謝</h2>
        <p>
          感謝您使用本服務！本專案旨在學習和分享，希望能幫助您更好地管理個人財務。
          如有任何建議或回饋，歡迎隨時聯絡。
        </p>
        <div class="notice-box">
          <p>
            <strong>提醒：</strong>本服務為個人學習專案，請謹慎使用並定期備份資料。
            如需專業的財務管理服務，建議使用商業級的記帳軟體或諮詢專業財務顧問。
          </p>
        </div>
      </section>

      <div class="footer-actions">
        <router-link to="/login" class="btn btn-primary">返回登入</router-link>
        <router-link to="/privacy" class="btn btn-secondary">查看隱私權政策</router-link>
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
