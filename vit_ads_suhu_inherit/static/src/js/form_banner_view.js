/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { STAGES, getStageImageSrc } from "./stage_config";

export class BannerFormRenderer extends FormController {
    static template = "vit_ads_suhu_inherit.BannerFormRenderer";
    static props = {...FormController.props};

    setup(){
        super.setup()
        console.log('inherited form view')
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
