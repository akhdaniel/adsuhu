/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

const PLATFORMS = {
    facebook: {
        label: "Facebook",
        icon: "fa-facebook",
        cls: "o_adsuhu_btn_facebook",
        load_route: "/facebook/pages",
        post_route: "/facebook/post_image",
        key: "pages",
    },
    instagram: {
        label: "Instagram",
        icon: "fa-instagram",
        cls: "o_adsuhu_btn_instagram",
        load_route: "/instagram/accounts",
        post_route: "/instagram/post_image",
        key: "accounts",
    },
    tiktok: {
        label: "TikTok",
        icon: "fa-music",
        cls: "o_adsuhu_btn_tiktok",
        load_route: "/tiktok/status",
        post_route: "/tiktok/post_image",
        key: "tiktok",
    },
};

export class SocialPoster extends Component {
    static template = "vit_adsuhu_ui.SocialPoster";
    static props = {
        image: { type: Object },
        onClose: { type: Function },
    };

    setup() {
        this.state = useState({
            platform: "facebook",
            targets: [],
            targetId: "",
            caption: "",
            loading: false,
            posting: false,
            alert: "",
            alertType: "info",
            authUrl: "",
            privacyOptions: [],
            privacyLevel: "",
            igUserId: "",
            tiktokReady: false,
        });
        this._buildCaption();
        this.loadTargets();
    }

    get platform() {
        return PLATFORMS[this.state.platform];
    }

    get platforms() {
        return Object.entries(PLATFORMS).map(([key, p]) => ({ key, ...p }));
    }

    _buildCaption() {
        const parts = [this.props.image.headline, this.props.image.primary_text].filter(
            Boolean
        );
        this.state.caption = parts.join("\n\n");
    }

    _csrf() {
        const el = document.getElementById("adsuhu-csrf-token");
        return el ? el.value : (odoo && odoo.csrf_token) || "";
    }

    async selectPlatform(key) {
        this.state.platform = key;
        this.state.targets = [];
        this.state.targetId = "";
        this.state.alert = "";
        this.state.authUrl = "";
        this.state.igUserId = "";
        this.state.tiktokReady = false;
        await this.loadTargets();
    }

    setAlert(message, type = "info") {
        this.state.alert = message;
        this.state.alertType = type;
    }

    async loadTargets() {
        this.state.loading = true;
        try {
            const response = await fetch(this.platform.load_route, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this._csrf(),
                },
                credentials: "same-origin",
                body: JSON.stringify({ return_url: window.location.href }),
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Failed to load account data.");
            }
            const json = await response.json();
            const data = json.result || json;
            if (data?.auth_required) {
                this.state.authUrl = data.auth_url || "";
                this.setAlert("Account not connected. Click the login link.", "warning");
                return;
            }
            if (data?.error) {
                throw new Error(data.error);
            }
            if (this.state.platform === "facebook") {
                this.state.targets = (data?.pages || []).map((p) => ({
                    id: p.id,
                    label: p.name,
                }));
            } else if (this.state.platform === "instagram") {
                this.state.targets = (data?.accounts || []).map((a) => ({
                    id: a.id,
                    label: a.name || a.username || a.id,
                }));
            } else {
                this.state.privacyOptions = data?.privacy_level_options || [];
                this.state.privacyLevel = data?.default_privacy_level || "";
                this.state.tiktokReady = data?.posting_ready !== false;
                if (!this.state.tiktokReady) {
                    this.setAlert(
                        data?.posting_message || "TikTok account is not ready to post.",
                        "warning"
                    );
                } else {
                    this.setAlert("TikTok connected. Ready to post.", "success");
                }
                return;
            }
            if (this.state.targets.length) {
                this.setAlert(
                    `Choose a target then post to ${this.platform.label}.`,
                    "success"
                );
            } else {
                this.setAlert(`No ${this.platform.label} target available.`, "warning");
            }
        } catch (err) {
            this.setAlert(err.message || "Failed to load account data.", "danger");
        } finally {
            this.state.loading = false;
        }
    }

    async submit(ev) {
        ev.preventDefault();
        if (this.state.posting) {
            return;
        }
        if (this.state.authUrl) {
            window.location.href = this.state.authUrl;
            return;
        }
        this.state.posting = true;
        try {
            const payload = {
                image_url: this.props.image.image_url || "",
                return_url: window.location.href,
            };
            if (this.state.platform === "facebook") {
                payload.page_id = this.state.targetId;
                payload.message = this.state.caption;
            } else if (this.state.platform === "instagram") {
                payload.page_id = this.state.targetId;
                payload.ig_user_id = this.state.targetId;
                payload.caption = this.state.caption;
            } else {
                payload.image_variant_id = this.props.image.id || "";
                payload.privacy_level = this.state.privacyLevel;
                payload.caption = this.state.caption;
            }
            const response = await fetch(this.platform.post_route, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": this._csrf(),
                },
                credentials: "same-origin",
                body: JSON.stringify(payload),
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Failed to post.");
            }
            const json = await response.json();
            const data = json.result || json;
            if (data?.auth_required && data?.auth_url) {
                this.state.authUrl = data.auth_url;
                this.setAlert("Auth required. Click the login link.", "warning");
                return;
            }
            if (data?.error) {
                throw new Error(data.error);
            }
            this.setAlert("Posted successfully!", "success");
            await sleep(1200);
            this.props.onClose();
        } catch (err) {
            this.setAlert(err.message || "Posting failed.", "danger");
        } finally {
            this.state.posting = false;
        }
    }
}
