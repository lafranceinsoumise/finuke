import Cleave from 'cleave.js'
import 'cleave.js/src/addons/phone-type-formatter.fr'


function phoneField(selector) {
  new Cleave(selector, {
    phone: true,
    phoneRegionCode: 'FR'
  })
}


function codeField(selector) {
  new Cleave(selector, {
    blocks: [3, 3],
    numericOnly: true,
  })
}

if (document.querySelector('input[name="phone_number"]'))
  phoneField('input[name="phone_number"]');

// if(document.querySelector('input[name="code"]'))
//   codeField('input[name="code"]');
