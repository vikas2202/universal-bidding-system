'use strict';

// Countdown timer management
const countdownTimers = {};

function formatTime(seconds) {
    if (seconds <= 0) return 'Ending...';
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (days > 0) return `${days}d ${hours}h ${mins}m`;
    if (hours > 0) return `${hours}h ${mins}m ${secs}s`;
    return `${mins}m ${secs}s`;
}

function startCountdown(el) {
    const endTimeStr = el.dataset.endTime;
    if (!endTimeStr) return;
    const endTime = new Date(endTimeStr).getTime();
    const id = el.dataset.auctionId || Math.random().toString(36).substr(2, 9);
    el.dataset.countdownId = id;

    function tick() {
        const now = Date.now();
        const remaining = Math.floor((endTime - now) / 1000);
        if (remaining <= 0) {
            el.textContent = 'Ended';
            el.classList.remove('countdown-urgent');
            clearInterval(countdownTimers[id]);
            return;
        }
        el.textContent = formatTime(remaining);
        if (remaining < 300) {
            el.classList.add('countdown-urgent');
        }
    }
    tick();
    countdownTimers[id] = setInterval(tick, 1000);
}

function initCountdowns() {
    document.querySelectorAll('.countdown-timer, .countdown-display').forEach(el => {
        if (el.dataset.endTime) startCountdown(el);
    });
}

// AJAX bid submission
function submitBid(form, auctionId) {
    const btn = form.querySelector('#bid-btn');
    const originalText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Placing bid...';
    }

    const formData = new FormData(form);
    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
        },
        body: formData,
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast('success', data.message || 'Bid placed!');
            updateAuctionDisplay(auctionId, data);
        } else {
            showToast('danger', data.error || 'Failed to place bid.');
        }
    })
    .catch(() => showToast('danger', 'Network error. Please try again.'))
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    });
}

function updateAuctionDisplay(auctionId, data) {
    if (data.new_price) {
        const priceEl = document.getElementById('current-price');
        if (priceEl) {
            priceEl.textContent = '$' + parseFloat(data.new_price).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
            priceEl.classList.add('price-updated');
            setTimeout(() => priceEl.classList.remove('price-updated'), 1500);
        }
    }
    if (data.bid_count !== undefined) {
        const countEl = document.getElementById('bid-count');
        if (countEl) countEl.textContent = data.bid_count + ' bid' + (data.bid_count !== 1 ? 's' : '');
    }
    if (data.end_time) {
        const countdown = document.getElementById('main-countdown');
        if (countdown) {
            countdown.dataset.endTime = data.end_time;
            const oldId = countdown.dataset.countdownId;
            if (oldId && countdownTimers[oldId]) clearInterval(countdownTimers[oldId]);
            startCountdown(countdown);
        }
    }
    // Update min bid input
    if (data.new_price) {
        const bidInput = document.getElementById('bid-amount');
        const proxyInput = document.getElementById('proxy-amount');
        const newMin = parseFloat(data.new_price) * 1.05;
        const minBid = Math.max(newMin, parseFloat(data.new_price) + 1.00);
        if (bidInput) {
            bidInput.min = minBid.toFixed(2);
            if (parseFloat(bidInput.value) < minBid) {
                bidInput.value = minBid.toFixed(2);
            }
        }
        if (proxyInput) {
            proxyInput.min = minBid.toFixed(2);
        }
    }
}

// Toast notifications
function showToast(type, message) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast bid-toast align-items-center text-bg-${type} border-0 mb-2`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>`;
    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, {delay: 4000});
    bsToast.show();
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

// Auto-refresh auction status every 15 seconds
function startAutoRefresh(auctionId) {
    if (!auctionId) return;
    setInterval(function() {
        fetch(`/bidding/api/status/${auctionId}/`, {
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        })
        .then(res => res.json())
        .then(data => {
            if (!data.is_active && data.status !== 'active') return;
            const priceEl = document.getElementById('current-price');
            const prevPrice = priceEl ? priceEl.dataset.price : null;
            if (priceEl && data.current_price !== prevPrice) {
                updateAuctionDisplay(auctionId, {
                    new_price: data.current_price,
                    bid_count: data.bid_count,
                    end_time: data.end_time,
                });
                priceEl.dataset.price = data.current_price;
            }
        })
        .catch(() => {});
    }, 15000);
}

// Notification count polling
function pollNotifications() {
    const badge = document.getElementById('notif-count');
    if (!badge) return;
    setInterval(function() {
        fetch('/notifications/unread-count/', {
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        })
        .then(res => res.json())
        .then(data => {
            if (data.count > 0) {
                badge.textContent = data.count > 99 ? '99+' : data.count;
                badge.style.display = 'inline';
            } else {
                badge.style.display = 'none';
            }
        })
        .catch(() => {});
    }, 30000);
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initCountdowns();
    pollNotifications();

    // Auto-refresh if on auction detail page
    const mainCountdown = document.getElementById('main-countdown');
    if (mainCountdown && mainCountdown.dataset.auctionId) {
        startAutoRefresh(mainCountdown.dataset.auctionId);
    }

    // Load initial notification count
    const badge = document.getElementById('notif-count');
    if (badge) {
        fetch('/notifications/unread-count/', {
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        })
        .then(res => res.json())
        .then(data => {
            if (data.count > 0) {
                badge.textContent = data.count > 99 ? '99+' : data.count;
                badge.style.display = 'inline';
            }
        })
        .catch(() => {});
    }
});
