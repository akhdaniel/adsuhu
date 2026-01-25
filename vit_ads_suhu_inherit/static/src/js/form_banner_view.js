/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { STAGES, getStageImageSrc } from "./stage_config";

export class BannerFormRenderer extends FormController {
    static template = "vit_ads_suhu_inherit.BannerFormRenderer";
    static props = {...FormController.props};

    setup(){
        super.setup();
        this.actionService = useService("action");
        const currentAction = this.actionService.currentController?.action;
        const currentUrl = window.location.href;
        const url = new URL(currentUrl);
        const segments = url.pathname.split("/").filter(Boolean);
        this._urlParts = [];
        if (segments.length) {
            this._urlParts.push(`${url.origin}/${segments[0]}`);
            for (let i = 1; i < segments.length; i += 2) {
                const pair = segments.slice(i, i + 2).join("/");
                if (pair) {
                    this._urlParts.push(pair);
                }
            }
        }
        if (url.searchParams.has("debug")) {
            this._urlParts.push(`debug=${url.searchParams.get("debug")}`);
        }
        console.log("inherited form view", {currentAction, currentUrl, urlParts: this._urlParts });
    }

    get urlParts() {
        return this._urlParts || [];
    }

    get stages() {
        return STAGES;
    }

    get imageSrc() {
        return getStageImageSrc(this.props.resModel);
    }
}

export const bannerFormView = {
    ...formView,
    Controller: BannerFormRenderer,
};

registry.category('views').add('ads_form_with_banner', bannerFormView)
