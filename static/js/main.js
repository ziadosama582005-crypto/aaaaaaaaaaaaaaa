/* main.js - JavaScript الرئيسي */

function updateCartBadge() {
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const count = cart.length;
    const badge = document.getElementById('cart-count');
    
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'inline-block' : 'none';
    }
}

// تحديث الشارة عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', updateCartBadge);

// نسخ النص
function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    alert('✅ تم النسخ');
}

// تنسيق المبالغ النقدية
function formatCurrency(amount) {
    return new Intl.NumberFormat('ar-SA', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}
