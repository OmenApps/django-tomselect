/**
 * Plugin: "dropdown_footer" (Tom Select)
 * Copyright (c) contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this
 * file except in compliance with the License. You may obtain a copy of the License at:
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
 * ANY KIND, either express or implied. See the License for the specific language
 * governing permissions and limitations under the License.
 *
 */

import { getDom } from 'tom-select/dist/esm/vanilla.js';

type DFOptions = {
	title	    ?: string,
	footerClass	?: string,
	html	 	?: (data:DFOptions) => string,
};

export default function(this:TomSelect, userOptions:DFOptions) {
    const self = this;

	const options = Object.assign({
		title         : 'Autocomplete Footer',
		footerClass   : 'container-fluid mt-1 px-2 border-top dropdown-footer',

		html: (data:DFOptions) => {
			return (
				'<div title="' + data.title + '" class="' + data.footerClass + '"></div>'
			);
		}
	}, userOptions);

	self.hook('after', 'setup', () => {
		var footer = getDom(options.html(options));

        self.dropdown.appendChild(footer);
	});

};
