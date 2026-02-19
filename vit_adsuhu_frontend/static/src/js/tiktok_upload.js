/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AdsuhuTiktokUpload = publicWidget.Widget.extend({
    selector: ".adsuhu-container",
    events: {
        "click .js-upload-tiktok": "_onOpenTiktokUpload",
    },
    start() {
        this.csrfToken = document.getElementById("adsuhu-csrf-token")?.value || "";
        this.selectedImageUrl = "";
        this.modalEl = document.getElementById("tiktok-upload-modal");
        this.alertEl = document.getElementById("tiktok-upload-alert");
        this.authWrapEl = document.getElementById("tiktok-upload-auth-wrap");
        this.authLinkEl = document.getElementById("tiktok-upload-auth-link");
        this.captionEl = document.getElementById("tiktok-upload-caption");
        this.privacySelectEl = document.getElementById("tiktok-upload-privacy-select");
        this.previewEl = document.getElementById("tiktok-upload-preview");
        this.submitBtn = document.querySelector(".js-tiktok-upload-submit");
        this.disconnectBtn = document.querySelector(".js-tiktok-disconnect");
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
        this.submitBtn.addEventListener("click", (event) => this._onSubmitTiktokUpload(event));
    },
    _bindDisconnectEvent() {
        if (!this.disconnectBtn || this._disconnectBound) {
            return;
        }
        this._disconnectBound = true;
        this.disconnectBtn.addEventListener("click", (event) => this._onDisconnectTiktok(event));
    },
    _bindModalCloseEvents() {
        if (!this.modalEl || this._modalCloseBound) {
            return;
        }
        this._modalCloseBound = true;
        this.modalEl.addEventListener("click", (event) => {
            const closeButton = event.target.closest(".js-tiktok-modal-close,[data-bs-dismiss='modal']");
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
        if (params.get("tt_connected") === "1") {
            this._showAlert("TikTok connected successfully. Anda bisa langsung post.", "success");
        } else if (params.get("tt_error")) {
            this._showAlert(`TikTok OAuth gagal: ${params.get("tt_error")}`, "danger");
        }
    },
    async _onOpenTiktokUpload(event) {
        event.preventDefault();
        const imageUrl = event.currentTarget?.dataset?.imageUrl || "";
        const imageVariantId = event.currentTarget?.dataset?.imageVariantId || "";
        const headline = (event.currentTarget?.dataset?.headline || "").trim();
        const primaryText = (event.currentTarget?.dataset?.primaryText || "").trim();
        if (!imageUrl) {
            this._showAlert("Image URL not found.", "danger");
            return;
        }

        this.selectedImageUrl = imageUrl;
        if (this.previewEl) {
            this.previewEl.src = imageUrl;
            this.previewEl.dataset.imageUrl = imageUrl;
            this.previewEl.dataset.imageVariantId = imageVariantId;
        }
        if (this.modalEl) {
            this.modalEl.dataset.imageUrl = imageUrl;
            this.modalEl.dataset.imageVariantId = imageVariantId;
            this.modalEl.dataset.headline = headline;
            this.modalEl.dataset.primaryText = primaryText;
        }
        if (this.submitBtn) {
            this.submitBtn.dataset.imageUrl = imageUrl;
            this.submitBtn.dataset.imageVariantId = imageVariantId;
        }
        if (this.captionEl) {
            const autoCaption = [headline, primaryText].filter(Boolean).join("\n\n");
            this.captionEl.value = autoCaption;
        }

        this._hideAuthPrompt();
        this._resetPrivacyOptions();
        this._setDisconnectDisabled(true);
        this._showAlert("Checking TikTok login...", "info");
        this._showModal();
        await this._loadTiktokStatus();
    },
    async _loadTiktokStatus() {
        try {
            const response = await fetch("/tiktok/status", {
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
                throw new Error(text || "Failed to check TikTok status.");
            }
            const rpcJson = await response.json();
            const json = this._unwrapRpcPayload(rpcJson);

            if (json?.auth_required) {
                this._setSubmitDisabled(true);
                this._setDisconnectDisabled(true);
                if (json?.auth_url) {
                    const popupAuthUrl = this._withPopupParam(json.auth_url);
                    const ok = await this._openTiktokAuthPopup(popupAuthUrl);
                    if (ok) {
                        this._markReadyToPost();
                    }
                    return;
                }
                this._showAuthPrompt(json.auth_url);
                this._showAlert("Login TikTok dulu untuk lanjut post.", "warning");
                return;
            }
            if (json?.error) {
                throw new Error(json.error);
            }

            this._hideAuthPrompt();
            this._setSubmitDisabled(false);
            this._setDisconnectDisabled(false);
            this._populatePrivacyOptions(
                json?.privacy_level_options || [],
                json?.default_privacy_level || ""
            );
            if (json?.posting_ready === false) {
                this._setSubmitDisabled(true);
                this._showAlert(
                    json?.posting_message || "Akun TikTok belum siap untuk posting dari aplikasi ini.",
                    "warning"
                );
                return;
            }
            const creator = json?.creator ? ` @${json.creator}` : "";
            this._showAlert(`TikTok connected${creator}. Klik Post to TikTok.`, "success");
        } catch (error) {
            this._setSubmitDisabled(true);
            this._setDisconnectDisabled(true);
            this._showAlert(error.message || "Failed to check TikTok status.", "danger");
        }
    },
    async _onDisconnectTiktok(event) {
        event.preventDefault();
        this._setDisconnectDisabled(true, "Disconnecting...");
        this._setSubmitDisabled(true);
        try {
            const response = await fetch("/tiktok/disconnect", {
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
                throw new Error(text || "Failed to disconnect TikTok.");
            }
            const rpcJson = await response.json();
            const json = this._unwrapRpcPayload(rpcJson);
            if (json?.error || json?.success === false) {
                throw new Error(json.error || "Failed to disconnect TikTok.");
            }
            this._resetPrivacyOptions();
            this._showAuthPrompt(this._buildAuthStartUrl(true));
            this._showAlert("TikTok account disconnected.", "warning");
        } catch (error) {
            this._showAlert(error.message || "Failed to disconnect TikTok.", "danger");
        } finally {
            this._setDisconnectDisabled(false);
        }
    },
    async _onSubmitTiktokUpload(event) {
        event.preventDefault();
        const imageUrl =
            this.selectedImageUrl ||
            this.submitBtn?.dataset?.imageUrl ||
            this.previewEl?.dataset?.imageUrl ||
            this.modalEl?.dataset?.imageUrl ||
            this.previewEl?.getAttribute("src") ||
            "";
        const imageVariantId =
            this.submitBtn?.dataset?.imageVariantId ||
            this.previewEl?.dataset?.imageVariantId ||
            this.modalEl?.dataset?.imageVariantId ||
            "";
        const privacyLevel = this.privacySelectEl?.value || "";

        if (!imageUrl && !imageVariantId) {
            this._showAlert("Image URL missing.", "danger");
            return;
        }
        if (!imageUrl && imageVariantId) {
            this._showAlert("Resolving image from server...", "info");
        }
        this.selectedImageUrl = imageUrl || "";
        this._setSubmitDisabled(true, "Posting...");
        try {
            const response = await fetch("/tiktok/post_image", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this.csrfToken,
                },
                body: JSON.stringify({
                    image_url: imageUrl || "",
                    image_variant_id: imageVariantId || "",
                    privacy_level: privacyLevel,
                    caption: this.captionEl?.value || "",
                    return_url: this._getReturnUrl(),
                }),
                credentials: "same-origin",
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Failed to post to TikTok.");
            }
            const rpcJson = await response.json();
            const json = this._unwrapRpcPayload(rpcJson);

            if (json?.auth_required && json?.auth_url) {
                const popupAuthUrl = this._withPopupParam(json.auth_url);
                const ok = await this._openTiktokAuthPopup(popupAuthUrl);
                if (ok) {
                    this._markReadyToPost();
                }
                return;
            }
            if (json?.error) {
                throw new Error(json.error);
            }

            this._showAlert("Image berhasil dikirim ke TikTok.", "success");
            setTimeout(() => this._hideModal(), 1200);
        } catch (error) {
            this._showAlert(error.message || "Failed to post to TikTok.", "danger");
        } finally {
            this._setSubmitDisabled(false);
        }
    },
    _getReturnUrl() {
        return `${window.location.pathname}${window.location.search}`;
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
    _markReadyToPost() {
        this._hideAuthPrompt();
        this._setSubmitDisabled(false);
        this._showModal();
        this._showAlert("TikTok connected. Sekarang siap post konten ini.", "success");
    },
    async _openTiktokAuthPopup(authUrl) {
        const popup = window.open(
            authUrl,
            "tiktok_oauth_popup",
            "width=600,height=760,menubar=no,toolbar=no,status=no"
        );
        if (!popup) {
            window.location.href = authUrl;
            return false;
        }

        this._showAlert("Silakan login TikTok di popup.", "info");
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
                if (data.type !== "tiktok_oauth_result") {
                    return;
                }
                if (data.success) {
                    try {
                        if (!popup.closed) {
                            popup.close();
                        }
                    } catch (error) {
                        // Ignore cross-window close errors.
                    }
                    window.focus();
                    this._showModal();
                    finish(true);
                } else {
                    this._showAlert(data.error || "TikTok login gagal.", "danger");
                    finish(false);
                }
            };
            window.addEventListener("message", onMessage);

            const closedPoll = setInterval(() => {
                let isClosed = false;
                try {
                    isClosed = !!popup.closed;
                } catch (error) {
                    return;
                }
                if (isClosed) {
                    clearInterval(closedPoll);
                    if (!resolved) {
                        this._showAlert("Popup login TikTok ditutup.", "warning");
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
            : '<i class="fa fa-send me-1"></i> Post to TikTok';
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
    _buildAuthStartUrl(forceLogin = false) {
        const params = new URLSearchParams({
            next: this._getReturnUrl(),
        });
        if (forceLogin) {
            params.set("force_login", "1");
        }
        return `/tiktok/oauth/start?${params.toString()}`;
    },
    _resetPrivacyOptions() {
        if (!this.privacySelectEl) {
            return;
        }
        this.privacySelectEl.innerHTML = '<option value="">Select privacy</option>';
    },
    _populatePrivacyOptions(options, selectedValue) {
        this._resetPrivacyOptions();
        if (!this.privacySelectEl) {
            return;
        }
        const values = Array.isArray(options) ? options : [];
        for (const value of values) {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = value;
            this.privacySelectEl.appendChild(option);
        }
        if (selectedValue && values.includes(selectedValue)) {
            this.privacySelectEl.value = selectedValue;
        } else if (values.length) {
            this.privacySelectEl.value = values.includes("SELF_ONLY") ? "SELF_ONLY" : values[0];
        }
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
    _showAlert(message, level) {
        if (!this.alertEl) {
            return;
        }
        this.alertEl.textContent = message || "";
        this.alertEl.className = `alert alert-${level || "info"}`;
        this.alertEl.classList.remove("d-none");
    },
});
