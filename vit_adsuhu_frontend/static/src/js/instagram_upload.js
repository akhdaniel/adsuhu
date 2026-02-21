/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AdsuhuInstagramUpload = publicWidget.Widget.extend({
    selector: ".adsuhu-container",
    events: {
        "click .js-upload-instagram": "_onOpenInstagramUpload",
    },
    start() {
        this.csrfToken = document.getElementById("adsuhu-csrf-token")?.value || "";
        this.selectedImageUrl = "";
        this.modalEl = document.getElementById("instagram-upload-modal");
        this.alertEl = document.getElementById("instagram-upload-alert");
        this.authWrapEl = document.getElementById("instagram-upload-auth-wrap");
        this.authLinkEl = document.getElementById("instagram-upload-auth-link");
        this.accountSelectEl = document.getElementById("instagram-upload-account-select");
        this.captionEl = document.getElementById("instagram-upload-caption");
        this.previewEl = document.getElementById("instagram-upload-preview");
        this.captionMetaEl = document.getElementById("facebook-caption-meta");
        this.submitBtn = document.querySelector(".js-instagram-upload-submit");
        this.disconnectBtn = document.querySelector(".js-instagram-disconnect");
        this._bindModalCloseEvents();
        this._bindSubmitEvent();
        this._bindDisconnectEvent();
        this._showOAuthFeedbackFromQuery();
        return this._super(...arguments);
    },
    _bindSubmitEvent() {
        if (!this.submitBtn || this._submitBound) {
            return;
        }
        this._submitBound = true;
        this.submitBtn.addEventListener("click", (event) => this._onSubmitInstagramUpload(event));
    },
    _bindDisconnectEvent() {
        if (!this.disconnectBtn || this._disconnectBound) {
            return;
        }
        this._disconnectBound = true;
        this.disconnectBtn.addEventListener("click", (event) => this._onDisconnectInstagram(event));
    },
    _bindModalCloseEvents() {
        if (!this.modalEl || this._modalCloseBound) {
            return;
        }
        this._modalCloseBound = true;
        this.modalEl.addEventListener("click", (event) => {
            const closeButton = event.target.closest(".js-instagram-modal-close,[data-bs-dismiss='modal']");
            if (closeButton) {
                event.preventDefault();
                this._hideModal();
                return;
            }
            if (event.target === this.modalEl && !window.bootstrap?.Modal) {
                this._hideModal();
            }
        });
    },
    _showOAuthFeedbackFromQuery() {
        const params = new URLSearchParams(window.location.search);
        if (params.get("ig_connected") === "1") {
            this._showAlert("Instagram connected successfully. Anda bisa langsung post.", "success");
        } else if (params.get("ig_error")) {
            this._showAlert(`Instagram OAuth gagal: ${params.get("ig_error")}`, "danger");
        }
    },
    async _onOpenInstagramUpload(event) {
        event.preventDefault();
        const button = event.currentTarget;
        const imageUrl = button?.dataset?.imageUrl || "";
        const headline = this._stripHtml(button?.dataset?.headline || "");
        const primaryText = this._stripHtml(button?.dataset?.primaryText || "");
        const landingPageUrl = this._stripHtml(this.captionMetaEl?.dataset?.productUrl || "");
        const productTags = this._normalizeTags(this.captionMetaEl?.dataset?.productTags || "");
        if (!imageUrl) {
            this._showAlert("Image URL not found.", "danger");
            return;
        }
        this.selectedImageUrl = imageUrl;
        if (this.previewEl) {
            this.previewEl.src = imageUrl;
        }
        if (this.captionEl) {
            this.captionEl.value = [headline, primaryText, landingPageUrl, productTags].filter(Boolean).join("\n\n");
        }
        this._resetAccountSelect();
        this._hideAuthPrompt();
        this._setDisconnectDisabled(true);
        this._showAlert("Loading your Instagram accounts...", "info");
        this._showModal();
        await this._loadInstagramAccounts();
    },
    async _loadInstagramAccounts() {
        try {
            const response = await fetch("/instagram/accounts", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this.csrfToken,
                },
                body: JSON.stringify({
                    return_url: this._getReturnUrl(),
                }),
                credentials: "same-origin",
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Failed to load Instagram accounts.");
            }
            const rpcJson = await response.json();
            const json = this._unwrapRpcPayload(rpcJson);
            if (json?.auth_required) {
                this._setSubmitDisabled(true);
                this._setDisconnectDisabled(true);
                if (json?.auth_url) {
                    const popupAuthUrl = this._withPopupParam(json.auth_url);
                    const ok = await this._openInstagramAuthPopup(popupAuthUrl);
                    if (ok) {
                        await this._loadInstagramAccounts();
                    }
                    return;
                }
                this._showAuthPrompt(json.auth_url);
                this._showAlert("Login Instagram dulu untuk lanjut post.", "warning");
                return;
            }
            if (json?.error) {
                this._setSubmitDisabled(true);
                this._setDisconnectDisabled(true);
                this._showAlert(json.error, "danger");
                return;
            }
            const accounts = json?.accounts || [];
            this._populateAccountSelect(accounts);
            if (!accounts.length) {
                this._showAlert("Tidak ada akun Instagram Business yang tersedia.", "warning");
                this._setSubmitDisabled(true);
                this._setDisconnectDisabled(false);
                return;
            }
            this._hideAuthPrompt();
            this._setSubmitDisabled(false);
            this._setDisconnectDisabled(false);
            this._showAlert("Pilih akun Instagram lalu klik Post to Instagram.", "success");
        } catch (error) {
            this._setSubmitDisabled(true);
            this._setDisconnectDisabled(true);
            this._showAlert(error.message || "Failed to load Instagram accounts.", "danger");
        }
    },
    async _onDisconnectInstagram(event) {
        event.preventDefault();
        this._setDisconnectDisabled(true, "Disconnecting...");
        this._setSubmitDisabled(true);
        try {
            const response = await fetch("/instagram/disconnect", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this.csrfToken,
                },
                body: JSON.stringify({
                    return_url: this._getReturnUrl(),
                }),
                credentials: "same-origin",
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Failed to disconnect Instagram.");
            }
            const rpcJson = await response.json();
            const json = this._unwrapRpcPayload(rpcJson);
            if (json?.error || json?.success === false) {
                throw new Error(json.error || "Failed to disconnect Instagram.");
            }
            this._hideModal();
        } catch (error) {
            this._showAlert(error.message || "Failed to disconnect Instagram.", "danger");
        } finally {
            this._setDisconnectDisabled(false);
        }
    },
    async _onSubmitInstagramUpload(event) {
        event.preventDefault();
        const selectedRaw = this.accountSelectEl?.value || "";
        let pageId = "";
        let igUserId = "";
        try {
            const parsed = JSON.parse(selectedRaw || "{}");
            pageId = parsed.page_id || "";
            igUserId = parsed.ig_user_id || "";
        } catch (_err) {
            pageId = "";
            igUserId = "";
        }
        const caption = this._stripHtml(this.captionEl?.value || "");
        if (!igUserId || !pageId) {
            this._showAlert("Pilih Instagram account dulu.", "danger");
            return;
        }
        if (!this.selectedImageUrl) {
            this._showAlert("Image URL missing.", "danger");
            return;
        }

        this._setSubmitDisabled(true, "Posting...");
        try {
            const response = await fetch("/instagram/post_image", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this.csrfToken,
                },
                body: JSON.stringify({
                    image_url: this.selectedImageUrl,
                    page_id: pageId,
                    ig_user_id: igUserId,
                    caption,
                    return_url: this._getReturnUrl(),
                }),
                credentials: "same-origin",
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Failed to post to Instagram.");
            }
            const rpcJson = await response.json();
            const json = this._unwrapRpcPayload(rpcJson);
            if (json?.auth_required && json?.auth_url) {
                const popupAuthUrl = this._withPopupParam(json.auth_url);
                const ok = await this._openInstagramAuthPopup(popupAuthUrl);
                if (ok) {
                    await this._loadInstagramAccounts();
                }
                return;
            }
            if (json?.error) {
                throw new Error(json.error);
            }
            this._showAlert("Image berhasil dipost ke Instagram.", "success");
            setTimeout(() => this._hideModal(), 1200);
        } catch (error) {
            this._showAlert(error.message || "Failed to post to Instagram.", "danger");
        } finally {
            this._setSubmitDisabled(false);
        }
    },
    _unwrapRpcPayload(payload) {
        if (payload && typeof payload === "object" && Object.prototype.hasOwnProperty.call(payload, "result")) {
            return payload.result || {};
        }
        return payload || {};
    },
    _withPopupParam(url) {
        const parsed = new URL(url, window.location.origin);
        parsed.searchParams.set("popup", "1");
        return parsed.pathname + parsed.search;
    },
    _getReturnUrl() {
        return `${window.location.pathname}${window.location.search}`;
    },
    _showModal() {
        if (!this.modalEl) {
            return;
        }
        if (window.bootstrap?.Modal) {
            window.bootstrap.Modal.getOrCreateInstance(this.modalEl).show();
            return;
        }
        this.modalEl.classList.add("show");
        this.modalEl.style.display = "block";
        this.modalEl.setAttribute("aria-modal", "true");
        this.modalEl.removeAttribute("aria-hidden");
        document.body.classList.add("modal-open");
    },
    _hideModal() {
        if (!this.modalEl) {
            return;
        }
        if (window.bootstrap?.Modal) {
            window.bootstrap.Modal.getOrCreateInstance(this.modalEl).hide();
            return;
        }
        this.modalEl.classList.remove("show");
        this.modalEl.style.display = "none";
        this.modalEl.setAttribute("aria-hidden", "true");
        this.modalEl.removeAttribute("aria-modal");
        document.body.classList.remove("modal-open");
        document.querySelectorAll(".modal-backdrop").forEach((el) => el.remove());
    },
    async _openInstagramAuthPopup(authUrl) {
        const popup = window.open(authUrl, "instagram_oauth_popup", "width=600,height=760,menubar=no,toolbar=no,status=no");
        if (!popup) {
            window.location.href = authUrl;
            return false;
        }
        this._showAlert("Silakan login Instagram di popup.", "info");
        return new Promise((resolve) => {
            let resolved = false;
            const cleanup = () => {
                window.removeEventListener("message", onMessage);
                clearInterval(closedPoll);
            };
            const finish = (value) => {
                if (resolved) {
                    return;
                }
                resolved = true;
                cleanup();
                resolve(value);
            };
            const onMessage = (event) => {
                if (event.origin !== window.location.origin) {
                    return;
                }
                const data = event.data || {};
                if (data.type !== "instagram_oauth_result") {
                    return;
                }
                if (data.success) {
                    this._showAlert("Instagram connected. Memuat akun...", "success");
                    finish(true);
                } else {
                    this._showAlert(data.error || "Instagram login gagal.", "danger");
                    finish(false);
                }
            };
            window.addEventListener("message", onMessage);
            const closedPoll = setInterval(() => {
                let isClosed = false;
                try {
                    isClosed = !!popup.closed;
                } catch (_err) {
                    return;
                }
                if (isClosed) {
                    clearInterval(closedPoll);
                    if (!resolved) {
                        this._showAlert("Popup login Instagram ditutup.", "warning");
                        finish(false);
                    }
                }
            }, 400);
        });
    },
    _setSubmitDisabled(disabled, text) {
        if (!this.submitBtn) {
            return;
        }
        this.submitBtn.disabled = disabled;
        this.submitBtn.innerHTML = text
            ? `<i class="fa fa-send me-1"></i> ${text}`
            : '<i class="fa fa-send me-1"></i> Post to Instagram';
    },
    _setDisconnectDisabled(disabled, text) {
        if (!this.disconnectBtn) {
            return;
        }
        this.disconnectBtn.disabled = disabled;
        this.disconnectBtn.innerHTML = text
            ? `<i class="fa fa-unlink me-1"></i> ${text}`
            : '<i class="fa fa-unlink me-1"></i> Disconnect';
    },
    _showAuthPrompt(authUrl) {
        if (!this.authWrapEl) {
            return;
        }
        if (this.authLinkEl && authUrl) {
            this.authLinkEl.href = authUrl;
        }
        this.authWrapEl.classList.remove("d-none");
    },
    _hideAuthPrompt() {
        if (this.authWrapEl) {
            this.authWrapEl.classList.add("d-none");
        }
    },
    _resetAccountSelect() {
        if (!this.accountSelectEl) {
            return;
        }
        this.accountSelectEl.innerHTML = '<option value="">Select Instagram account</option>';
    },
    _populateAccountSelect(accounts) {
        this._resetAccountSelect();
        if (!this.accountSelectEl) {
            return;
        }
        for (const item of accounts || []) {
            const option = document.createElement("option");
            option.value = JSON.stringify({
                page_id: item.page_id || "",
                ig_user_id: item.ig_user_id || "",
            });
            const pageName = item.page_name ? ` - ${item.page_name}` : "";
            option.textContent = `${item.ig_username || item.ig_user_id}${pageName}`;
            this.accountSelectEl.appendChild(option);
        }
    },
    _showAlert(message, level) {
        if (!this.alertEl) {
            return;
        }
        this.alertEl.textContent = message || "";
        this.alertEl.className = `alert alert-${level || "info"}`;
        this.alertEl.classList.remove("d-none");
    },
    _stripHtml(value) {
        const text = String(value || "");
        if (!text) {
            return "";
        }
        return text
            .replace(/<[^>]*>/g, "")
            .replace(/\r/g, "")
            .split("\n")
            .map((line) => line.replace(/\s+/g, " ").trim())
            .filter(Boolean)
            .join("\n");
    },
    _normalizeTags(rawTags) {
        const plain = this._stripHtml(rawTags);
        if (!plain) {
            return "";
        }
        return plain
            .split(/[\n,;]+/)
            .map((tag) => tag.trim())
            .filter(Boolean)
            .map((tag) => {
                let cleaned = tag.replace(/^#+/, "");
                cleaned = cleaned.replace(/\s+/g, "");
                return cleaned ? `#${cleaned}` : "";
            })
            .filter(Boolean)
            .join(" ");
    },
});
