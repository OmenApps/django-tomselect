import TomSelect from 'tom-select';  // Use the full package instead of base
/* eslint-disable camelcase */
import TomSelect_checkbox_options from 'tom-select/plugins/checkbox_options/plugin.js'
import TomSelect_clear_button from 'tom-select/plugins/clear_button/plugin.js'
import TomSelect_dropdown_header from 'tom-select/plugins/dropdown_header/plugin.js'
import TomSelect_dropdown_input from 'tom-select/plugins/dropdown_input/plugin.js'
import TomSelect_remove_button from 'tom-select/plugins/remove_button/plugin.js'
import TomSelect_virtual_scroll from 'tom-select/plugins/virtual_scroll/plugin.js'
import TomSelect_dropdown_footer from './plugins/dropdown_footer/plugin.js'
/* eslint-enable camelcase */

// Define plugins
TomSelect.define('checkbox_options', TomSelect_checkbox_options)
TomSelect.define('clear_button', TomSelect_clear_button)
TomSelect.define('dropdown_header', TomSelect_dropdown_header)
TomSelect.define('dropdown_input', TomSelect_dropdown_input)
TomSelect.define('remove_button', TomSelect_remove_button)
TomSelect.define('virtual_scroll', TomSelect_virtual_scroll)
TomSelect.define('dropdown_footer', TomSelect_dropdown_footer)

// Export to window with constructor check
if (typeof TomSelect === 'function') {
    window.TomSelect = TomSelect;
} else {
    window.TomSelect = TomSelect.default || TomSelect;
}
