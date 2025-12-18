/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { STAGES } from "./stage_config";

export class BannerListRenderer extends ListController {
    static template = "vit_ads_suhu_inherit.BannerListRenderer";
    static props = { ...ListController.props };

    setup() {
        super.setup();
    }


    get stages() {
        return STAGES;
    }
}

export const bannerListView = {
    ...listView,
    Controller: BannerListRenderer,
};

registry.category('views').add('ads_list_with_banner', bannerListView)
