/**
 * BARBERO → Google Sheets (הזמנות אוטומטיות)
 *
 * התקנה (פעם אחת):
 * 1. צרו גיליון חדש ב-Google Sheets בשם למשל "BARBERO הזמנות"
 * 2. בשורה 1 הדביקו את הכותרות (אפשר להעתיק מהפונקציה ensureHeader_ למטה)
 * 3. Extensions → Apps Script → מחקו את הקוד הקיים והדביקו את הקובץ הזה
 * 4. שמרו → Deploy → New deployment → Type: Web app
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 5. העתיקו את ה-Web App URL (מסתיים ב-/exec)
 * 6. ב-Vercel → Environment Variables:
 *      GOOGLE_SHEETS_WEBHOOK_URL = <ה-URL מהשלב הקודם>
 *      GOOGLE_SHEETS_WEBHOOK_SECRET = (אופציונלי) מחרוזת סודית שתבחרו
 * 7. אם הגדרתם SECRET — שימו את אותה מחרוזת גם ב-WEBHOOK_SECRET למטה
 * 8. Redeploy ב-Vercel
 *
 * כל הזמנה מהאתר תוסיף שורה חדשה לגיליון.
 */

var SHEET_NAME = "הזמנות";
var WEBHOOK_SECRET = ""; // אופציונלי — חייב להתאים ל-GOOGLE_SHEETS_WEBHOOK_SECRET ב-Vercel

var HEADERS = [
  "סטטוס",
  "תאריך",
  "מספר הזמנה",
  "שם",
  "טלפון",
  "עיר",
  "כתובת",
  "דירה/קומה",
  "מיקוד",
  "הערות",
  "מוצרים",
  "סיכום ביניים",
  "משלוח",
  "סה״כ",
  "תשלום",
];

function doPost(e) {
  try {
    var body = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    if (WEBHOOK_SECRET && body.secret !== WEBHOOK_SECRET) {
      return json_({ ok: false, error: "unauthorized" });
    }

    var row = body.row || {};
    var sheet = getSheet_();
    ensureHeader_(sheet);

    sheet.appendRow([
      row.status || "ממתין לביט",
      row.createdAt || "",
      row.orderNumber || "",
      row.name || "",
      row.phone || "",
      row.city || "",
      row.address || "",
      row.unit || "",
      row.postal || "",
      row.notes || "",
      row.items || "",
      row.subtotal === "" || row.subtotal == null ? "" : Number(row.subtotal),
      row.shipping === "" || row.shipping == null ? "" : Number(row.shipping),
      row.total === "" || row.total == null ? "" : Number(row.total),
      row.payment || "ביט",
    ]);

    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message ? err.message : err) });
  }
}

function doGet() {
  return json_({ ok: true, service: "barbero-orders", sheet: SHEET_NAME });
}

function getSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  return sheet;
}

function ensureHeader_(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight("bold");
    sheet.setFrozenRows(1);
  }
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON,
  );
}
