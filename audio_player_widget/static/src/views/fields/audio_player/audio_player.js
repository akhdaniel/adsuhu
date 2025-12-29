/** @odoo-module **/

import { registry } from '@web/core/registry';
import { UrlField, urlField } from '@web/views/fields/url/url_field';
export class FieldAudioURL extends UrlField {
    static template = 'audio_player_widget.FieldAudioURL';
    setup(){
        super.setup()
    }
}
export const fieldAudioURL = {
    ...urlField,
    component: FieldAudioURL,
};
registry.category('fields').add('audio_player', fieldAudioURL);
