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

    get stages(){
        return [
            {id:'vit.product_value_analysis', label: 'Product Value Analysis'},
            {id:'vit.market_mapper', label:'Market Mapper'},
            {id:'vit.audience_profiler', label:'Audience Profiler'},
            {id:'vit.angle_hook', label:'Angle & Hook'},
            {id:'vit.ads_copy', label:'Ads Copy'},
            {id:'vit.script_writer', label:'Script Writer'},
            {id:'vit.visual_concept', label:'Visual Concept'},
            {id:'vit.compliance_checker', label:'Compliance Checker'},
            {id:'vit.landing_page_builder', label:'Landing Page Builder'},
            {id:'vit.campaign_builder', label:'Campaign Builder'},
        ]
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
