/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";
import { STAGES } from "./stage_config";

const existingListView = registry.category("views").get("ads_list_with_banner");
const BaseListController = existingListView?.Controller || ListController;

export class BannerListRenderer extends BaseListController {
    static template = "vit_ads_suhu_inherit.BannerListRenderer";
    static props = { ...BaseListController.props };

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.tokenBalance = null;
        onWillStart(async () => {
            await this._loadTokenBalance();
        });
    }


    get stages() {
        return STAGES;
    }

    get tokenDisplay() {
        if (this.tokenBalance === null || this.tokenBalance === undefined) {
            return "-";
        }
        return this.tokenBalance;
    }

    async _loadTokenBalance() {
        try {
            const balance = await this.orm.call(
                "res.users",
                "get_my_token_balance",
                []
            );
            this.tokenBalance = balance ?? 0;
        } catch (err) {
            this.tokenBalance = null;
        }
    }

    async openTokenLog() {
        try {
            await this.actionService.doAction(
                "vit_ads_suhu_token.action_vit_ai_token_log"
            );
        } catch (err) {
            // no-op
        }
    }

    // No redirect for now; display-only box.
}

export const bannerListView = {
    ...(existingListView || listView),
    Controller: BannerListRenderer,
};

if (existingListView) {
    existingListView.Controller = BannerListRenderer;
} else {
    registry.category('views').add('ads_list_with_banner', bannerListView);
}
