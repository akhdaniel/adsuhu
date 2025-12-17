/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from '@web/views/list/list_controller';

export class BannerListRenderer extends ListController {
    static template = "vit_ads_suhu_inherit.BannerListRenderer";
    static props = {...ListController.props};

    setup(){
        super.setup()
        console.log('inherited list view')
    }

    get imageSrc(){
        return `/vit_ads_suhu_inherit/static/src/img/${this.props.resModel}.png`
    }
}

export const bannerListView = {
    ...listView,
    Controller: BannerListRenderer,
};

registry.category('views').add('ads_list_with_banner', bannerListView)
