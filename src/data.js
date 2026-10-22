export const announcements = [
  "100% יבוא מקורי מארה״ב",
  "משלוחים לכל הארץ (7–14 ימי עסקים)",
  "תשלום מאובטח ב-Bit",
  "החזרה/החלפה תוך 14 ימים באריזה מקורית וסגורה בלבד",
  "אחריות ושירות לקוחות בעברית",
];

export const FREE_SHIPPING = 499;
export const SHIPPING_FEE = 39;

export function shippingFeeFor(subtotal) {
  if (subtotal > 0 && subtotal < FREE_SHIPPING) return SHIPPING_FEE;
  return 0;
}

export const categories = ["הכל", "מכונות תספורת", "טרימרים ומכונות גילוח"];

export const navLinks = [
  { label: "קולקציה", href: "#collection" },
  { label: "מכונות תספורת", href: "#collection", category: "מכונות תספורת" },
  { label: "אודות", href: "#about" },
];

export const trustItems = [
  {
    icon: "truck",
    title: "משלוח בינלאומי",
    text: "משלוח ישיר מארה״ב עד הבית, בדרך כלל תוך 7–14 ימי עסקים כולל מספר מעקב.",
  },
  {
    icon: "box",
    title: "אריזה מקורית",
    text: "מוצרים חדשים באריזה מקורית וסגורה מהיצרן.",
  },
  {
    icon: "globe",
    title: "יבוא ישיר מארה״ב",
    text: "סחורה מקורית בלבד, מהמותג ועד אליכם. לא שוק אפור, לא מקביל, ולא חיקוי שנראה דומה.",
  },
  {
    icon: "shield",
    title: "אחריות ושירות",
    text: "אחריות מלאה ושירות לקוחות בעברית לכל פנייה.",
  },
];

export const serviceLinks = [
  { label: "מעקב הזמנה", page: "tracking" },
  { label: "משלוחים והחזרות", page: "shipping" },
  { label: "אחריות", page: "warranty" },
  { label: "שאלות נפוצות", page: "faq" },
  { label: "מדיניות פרטיות", page: "privacy" },
  { label: "תקנון", page: "terms" },
];

export const pages = {
  tracking: {
    title: "מעקב הזמנה",
    paragraphs: [
      "הזינו את מספר ההזמנה ממסך האישור. המעקב בדמו הזה נשמר בדפדפן בלבד.",
    ],
  },
  shipping: {
    title: "משלוחים והחזרות",
    paragraphs: [
      "משלוח לכל הארץ תוך 2–5 ימי עסקים. בקנייה מעל 499 ₪ המשלוח עלינו, ומתחת לסכום זה עלות המשלוח 39 ₪.",
      "חלון החלפה של 14 יום מיום קבלת המוצר, כשהפריט באריזתו המקורית ולא נעשה בו שימוש. מוצרי טיפוח שנפתחו אינם ניתנים להחזרה מטעמי היגיינה.",
      "איסוף עצמי אינו פעיל בתצוגה הזו. בקופה בוחרים כתובת למשלוח בלבד.",
    ],
  },
  warranty: {
    title: "אחריות רשמית",
    paragraphs: [
      "מכונות תספורת, גילוח וטרימרים מגיעים עם אחריות יבואן לשנתיים על מנוע ורכיבים חשמליים. בלאי סביר של להב או רשת אינו כלול.",
      "האחריות תקפה ליבוא של BARBERO בלבד, מול חשבונית. פונים אלינו בעברית, ואנחנו מתאמים בדיקה או החלפה בלי לשלוח אתכם למותג בחו״ל.",
    ],
  },
  faq: {
    title: "שאלות נפוצות",
    paragraphs: [
      "האם המכונה עובדת בישראל? כן. הדגמים בקטלוג הם 100V–240V ומתחברים לשקע ישראלי בלי ממיר.",
      "האם זה יבוא מקורי? כן. הסחורה מגיעה 100% מקורית מארה״ב, עם אחריות מלאה שלנו ושירות לקוחות בעברית.",
      "תוך כמה זמן זה מגיע? המשלוח מגיע ישירות מארה״ב עד הבית, בדרך כלל תוך 7–14 ימי עסקים כולל מספר מעקב צמוד.",
      "אפשר להחליף דגם? כן, תוך 14 יום, כל עוד המוצר לא היה בשימוש והאריזה שמורה.",
      "איך משלמים? כרגע מקבלים תשלום בביט בלבד.",
    ],
  },
  privacy: {
    title: "מדיניות פרטיות",
    paragraphs: [
      "אנו ב-BARBERO מחויבים לשמירה מלאה על פרטיותכם. הפרטים האישיים משמשים אך ורק לצורך עיבוד המשלוח. כל פעולות התשלום מבוצעות בסליקה מוצפנת ומאובטחת (SSL) ואינן נשמרות בשרת. איננו מעבירים מידע לגורם שלישי.",
    ],
  },
  terms: {
    title: "תקנון",
    paragraphs: [
      "ברוכים הבאים ל-BARBERO. האתר מציע ציוד תספורת וגילוח מקורי ביבוא ישיר מארה״ב.",
      "• כל ההזמנות מטופלות ונשלחות ישירות לבית הלקוח תוך 7–14 ימי עסקים.",
      "• ניתן להחזיר או להחליף מוצר תוך 14 יום באריזתו המקורית ושלא נעשה בו שימוש.",
      "• כל המוצרים באתר מקוריים ומלווים באחריות מלאה ובשירות לקוחות בעברית.",
    ],
  },
};

export const products = [
  {
    id: "wahl-senior",
    name: "מכונת תספורת Wahl Cordless Senior 5-Star",
    brand: "Wahl",
    category: "מכונות תספורת",
    rating: 4.9,
    sku: "BRB-W-SN",
    voltage: "100V-240V (מתח אוניברסלי)",
    origin: "ארה״ב",
    badge: "חדש",
    stock: 8,
    price: 550,
    frame: "studio",
    image: "/products/wahl-senior-hero.webp",
    images: [
      "/products/wahl-senior-hero.webp",
      "/products/wahl-senior.webp",
      "/products/wahl-senior-use.webp",
    ],
    blurb:
      "מכונת תספורת אלחוטית מקצועית מסדרת 5-Star. גוף מתכת מחוזק, מנוע עוצמתי ולהב מבוקש לדירוגים מדויקים (Fade). אחיזה נוחה וארגונומית לעבודה ממושכת.",
  },
  {
    id: "fast-feed",
    name: "מכונת תספורת Wahl 5-Star Detailer Li",
    brand: "Wahl",
    category: "טרימרים ומכונות גילוח",
    rating: 4.6,
    reviews: 88,
    sku: "BRB-W-DL",
    voltage: null,
    origin: "ארה״ב",
    badge: null,
    stock: 0,
    price: 499,
    image:
      "https://images.unsplash.com/photo-1493256338651-d82f7acb2b38?auto=format&fit=crop&w=1000&q=80",
    blurb:
      "דיטיילר אלחוטי מסדרת 5-Star, לקווים חדים ולעבודה צמודה. אזלה מהמלאי כרגע — אפשר לשמור אותה לרשימת המשאלות.",
  },
];

export function formatPrice(value) {
  const amount = new Intl.NumberFormat("he-IL", { maximumFractionDigits: 0 }).format(value);
  return `₪${amount}`;
}

export function findProduct(id) {
  return products.find((product) => product.id === id) ?? null;
}

export function resolveOffer(product, variantId) {
  const variant =
    product.variants?.find((item) => item.id === variantId) ||
    product.variants?.[0] ||
    null;

  if (variant) {
    return {
      variant,
      price: variant.price,
      compareAt: variant.compareAt ?? null,
      label: variant.label,
    };
  }

  return {
    variant: null,
    price: product.price,
    compareAt: product.compareAt ?? null,
    label: null,
  };
}

export function discountPercent(price, compareAt) {
  if (!compareAt || compareAt <= price) return 0;
  return Math.round((1 - price / compareAt) * 100);
}

export function fromPrice(product) {
  if (product.variants?.length) {
    return Math.min(...product.variants.map((variant) => variant.price));
  }
  return product.price;
}
