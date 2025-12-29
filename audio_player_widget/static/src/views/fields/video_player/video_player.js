/** @odoo-module **/

import { registry } from '@web/core/registry';
import { UrlField, urlField } from '@web/views/fields/url/url_field';
export class FieldVideoURL extends UrlField {
    static template = 'audio_player_widget.FieldVideoURL';
    setup(){
        super.setup()
    }
}
export const fieldVideoURL = {
    ...urlField,
    component: FieldVideoURL,
};
registry.category('fields').add('video_player', fieldVideoURL);
