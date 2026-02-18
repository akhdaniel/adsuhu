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
        } else if (this.modalEl) {
            this.modalEl.classList.add("show");
            this.modalEl.style.display = "block";
            this.modalEl.setAttribute("aria-modal", "true");
            this.modalEl.removeAttribute("aria-hidden");
            document.body.classList.add("modal-open");
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
                if (json?.auth_url) {
                    const popupAuthUrl = this._withPopupParam(json.auth_url);
                    const ok = await this._openFacebookAuthPopup(popupAuthUrl);
                    if (ok) {
                        await this._loadFacebookPages();
                    }
                    return;
                }
                this._showAuthPrompt(json.auth_url);
                this._showAlert(
                    json?.reason === "no_pages"
                        ? "Belum ada Page terdeteksi. Login ulang Facebook lalu pilih akun yang punya Page."
                        : "Login Facebook dulu untuk lanjut upload.",
                    "warning"
                );
                this._setSubmitDisabled(true);
                return;
            }
            if (json?.error) {
                this._showAlert(json.error, "danger");
                this._setSubmitDisabled(true);
                return;
            }
            const pages = json?.pages || [];
            this._populatePageSelect(pages);
            if (!pages.length) {
                this._showAlert("Tidak ada Facebook Page yang bisa diakses akun ini.", "warning");
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
                const popupAuthUrl = this._withPopupParam(json.auth_url);
                const ok = await this._openFacebookAuthPopup(popupAuthUrl);
                if (ok) {
                    await this._loadFacebookPages();
                }
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
    _withPopupParam(url) {
        const parsed = new URL(url, window.location.origin);
        parsed.searchParams.set("popup", "1");
        return parsed.pathname + parsed.search;
    },
    async _openFacebookAuthPopup(authUrl) {
        const popup = window.open(
            authUrl,
            "facebook_oauth_popup",
            "width=600,height=760,menubar=no,toolbar=no,status=no"
        );
        if (!popup) {
            window.location.href = authUrl;
            return false;
        }

        this._showAlert("Silakan login Facebook di popup.", "info");
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
                if (data.type !== "facebook_oauth_result") {
                    return;
                }
                if (data.success) {
                    this._showAlert("Facebook connected. Memuat daftar Page...", "success");
                    finish(true);
                } else {
                    this._showAlert(data.error || "Facebook login gagal.", "danger");
                    finish(false);
                }
            };
            window.addEventListener("message", onMessage);

            const closedPoll = setInterval(() => {
                let isClosed = false;
                try {
                    isClosed = !!popup.closed;
                } catch (error) {
                    // Cross-origin popup can throw while on facebook.com; ignore and keep waiting.
                    return;
                }
                if (isClosed) {
                    clearInterval(closedPoll);
                    if (!resolved) {
                        this._showAlert("Popup login Facebook ditutup.", "warning");
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
