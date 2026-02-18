/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AdsuhuFacebookUpload = publicWidget.Widget.extend({
    selector: ".adsuhu-container",
    events: {
        "click .js-upload-facebook": "_onOpenFacebookUpload",
        "click .js-facebook-upload-submit": "_onSubmitFacebookUpload",
    },
    start() {
        this.csrfToken = document.getElementById("adsuhu-csrf-token")?.value || "";
        this.selectedImageUrl = "";
        this.modalEl = document.getElementById("facebook-upload-modal");
        this.alertEl = document.getElementById("facebook-upload-alert");
        this.authWrapEl = document.getElementById("facebook-upload-auth-wrap");
        this.authLinkEl = document.getElementById("facebook-upload-auth-link");
        this.pageSelectEl = document.getElementById("facebook-upload-page-select");
        this.captionEl = document.getElementById("facebook-upload-caption");
        this.previewEl = document.getElementById("facebook-upload-preview");
        this.submitBtn = document.querySelector(".js-facebook-upload-submit");
        this._showOAuthFeedbackFromQuery();
        return this._super(...arguments);
    },
    _showOAuthFeedbackFromQuery() {
        const params = new URLSearchParams(window.location.search);
        if (params.get("fb_connected") === "1") {
            this._showAlert("Facebook connected successfully. Anda bisa langsung upload ke Page.", "success");
        } else if (params.get("fb_error")) {
            this._showAlert(`Facebook OAuth gagal: ${params.get("fb_error")}`, "danger");
        }
    },
    async _onOpenFacebookUpload(event) {
        event.preventDefault();
        const button = event.currentTarget;
        const imageUrl = button?.dataset?.imageUrl || "";
        if (!imageUrl) {
            this._showAlert("Image URL not found.", "danger");
            return;
        }
        this.selectedImageUrl = imageUrl;
        if (this.previewEl) {
            this.previewEl.src = imageUrl;
        }
        if (this.captionEl) {
            this.captionEl.value = "";
        }
        this._resetPageSelect();
        this._hideAuthPrompt();
        this._showAlert("Loading your Facebook Pages...", "info");

        if (this.modalEl && window.bootstrap?.Modal) {
            window.bootstrap.Modal.getOrCreateInstance(this.modalEl).show();
        }

        await this._loadFacebookPages();
    },
    async _loadFacebookPages() {
        try {
            const payload = {
                return_url: this._getReturnUrl(),
            };
            const response = await fetch("/facebook/pages", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this.csrfToken,
                },
                body: JSON.stringify(payload),
                credentials: "same-origin",
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Failed to load Facebook pages.");
            }
            const json = await response.json();
            if (json?.auth_required) {
                this._showAuthPrompt(json.auth_url);
                this._showAlert("Login Facebook dulu untuk lanjut upload.", "warning");
                this._setSubmitDisabled(true);
                return;
            }
            const pages = json?.pages || [];
            this._populatePageSelect(pages);
            if (!pages.length) {
                this._showAlert("Akun ini belum punya Facebook Page yang bisa di-manage.", "warning");
                this._setSubmitDisabled(true);
                return;
            }
            this._hideAuthPrompt();
            this._showAlert("Pilih page lalu klik Post to Facebook.", "success");
            this._setSubmitDisabled(false);
        } catch (error) {
            this._showAlert(error.message || "Failed to load Facebook pages.", "danger");
            this._setSubmitDisabled(true);
        }
    },
    async _onSubmitFacebookUpload(event) {
        event.preventDefault();
        const pageId = this.pageSelectEl?.value || "";
        const message = this.captionEl?.value || "";
        if (!pageId) {
            this._showAlert("Pilih Facebook Page dulu.", "danger");
            return;
        }
        if (!this.selectedImageUrl) {
            this._showAlert("Image URL missing.", "danger");
            return;
        }

        this._setSubmitDisabled(true, "Posting...");
        try {
            const response = await fetch("/facebook/post_image", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this.csrfToken,
                },
                body: JSON.stringify({
                    image_url: this.selectedImageUrl,
                    page_id: pageId,
                    message,
                    return_url: this._getReturnUrl(),
                }),
                credentials: "same-origin",
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Failed to post to Facebook.");
            }
            const json = await response.json();
            if (json?.auth_required && json?.auth_url) {
                window.location.href = json.auth_url;
                return;
            }
            if (json?.error) {
                throw new Error(json.error);
            }

            this._showAlert("Image berhasil dipost ke Facebook Page.", "success");
            if (this.modalEl && window.bootstrap?.Modal) {
                setTimeout(() => {
                    window.bootstrap.Modal.getOrCreateInstance(this.modalEl).hide();
                }, 1200);
            }
        } catch (error) {
            this._showAlert(error.message || "Failed to post to Facebook.", "danger");
        } finally {
            this._setSubmitDisabled(false);
        }
    },
    _getReturnUrl() {
        return `${window.location.pathname}${window.location.search}`;
    },
    _setSubmitDisabled(disabled, text) {
        if (!this.submitBtn) {
            return;
        }
        this.submitBtn.disabled = disabled;
        this.submitBtn.innerHTML = text
            ? `<i class="fa fa-send me-1"></i> ${text}`
            : "<i class=\"fa fa-send me-1\"></i> Post to Facebook";
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
    _resetPageSelect() {
        if (!this.pageSelectEl) {
            return;
        }
        this.pageSelectEl.innerHTML = "<option value=\"\">Select Facebook Page</option>";
    },
    _populatePageSelect(pages) {
        this._resetPageSelect();
        if (!this.pageSelectEl) {
            return;
        }
        for (const page of pages) {
            const option = document.createElement("option");
            option.value = page.id;
            option.textContent = page.category ? `${page.name} (${page.category})` : page.name;
            this.pageSelectEl.appendChild(option);
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
});
