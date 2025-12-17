/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from '@web/views/form/form_controller';

export class BannerFormRenderer extends FormController {
    static template = "vit_ads_suhu_inherit.BannerFormRenderer";
    static props = {...FormController.props};

    setup(){
        super.setup()
        console.log('inherited form view')
    }

    get imageSrc(){
        return `/vit_ads_suhu_inherit/static/src/img/${this.props.resModel}.png`
    }
}

export const bannerFormView = {
    ...formView,
    Controller: BannerFormRenderer,
};

registry.category('views').add('ads_form_with_banner', bannerFormView)
