import PropTypes from 'prop-types';
import React from 'react';

import InputField from './inputField';
import SelectControl from './selectControl';

export default class Select2Field extends InputField {
  static propTypes = {
    ...InputField.propTypes,
    choices: PropTypes.array,
    allowClear: PropTypes.bool,
    allowEmpty: PropTypes.bool,
    multiple: PropTypes.bool,
  };

  static defaultProps = {
    ...InputField.defaultProps,
    allowClear: false,
    allowEmpty: false,
    placeholder: '--',
    escapeMarkup: true,
    multiple: false,
  };

  getField() {
    return <SelectControl value={this.state.value} {...this.props} id={this.getId()} />;
  }
}
