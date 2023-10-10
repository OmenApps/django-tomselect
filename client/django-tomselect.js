import TomSelect from 'tom-select/dist/js/tom-select.base.js';

/* eslint-disable camelcase */
import checkbox_options from 'tom-select/src/plugins/checkbox_options/plugin';
import clear_button from 'tom-select/src/plugins/clear_button/plugin';
import dropdown_header from 'tom-select/src/plugins/dropdown_header/plugin';
import dropdown_input from 'tom-select/src/plugins/dropdown_input/plugin';
import remove_button from 'tom-select/src/plugins/remove_button/plugin';
import virtual_scroll from 'tom-select/src/plugins/virtual_scroll/plugin';
import dropdown_footer from './plugins/dropdown_footer/plugin';
/* eslint-enable camelcase */

TomSelect.define('checkbox_options', checkbox_options);
TomSelect.define('clear_button', clear_button);
TomSelect.define('dropdown_header', dropdown_header);
TomSelect.define('dropdown_input', dropdown_input);
TomSelect.define('remove_button', remove_button);
TomSelect.define('virtual_scroll', virtual_scroll);
TomSelect.define('dropdown_footer', dropdown_footer);

window.TomSelect = require('tom-select/dist/js/tom-select.base.js')
