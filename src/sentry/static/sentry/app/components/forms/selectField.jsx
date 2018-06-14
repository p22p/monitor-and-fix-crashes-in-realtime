import React from 'react';
import PropTypes from 'prop-types';

import FormField from 'app/components/forms/formField';
import SelectControl from 'app/components/forms/selectControl';

export default class SelectField extends FormField {
  static propTypes = {
    ...FormField.propTypes,
    options: PropTypes.arrayOf(
      PropTypes.shape({
        label: PropTypes.node,
        value: PropTypes.any,
      })
    ),
    choices: PropTypes.arrayOf(PropTypes.oneOfType([PropTypes.string, PropTypes.array])),
    onChange: PropTypes.func,
    clearable: PropTypes.bool,
    creatable: PropTypes.bool,
  };

  static defaultProps = {
    ...FormField.defaultProps,
    clearable: true,
  };

  getClassName() {
    return '';
  }

  onChange = opt => {
    const value = opt ? opt.value : null;
    this.setValue(value);
  };

  getField() {
    const {options, creatable, choices, placeholder, disabled, required} = this.props;

    return (
      <SelectControl
        creatable={creatable}
        id={this.getId()}
        choices={choices}
        options={options}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        value={this.state.value}
        onChange={this.onChange}
        clearable={this.props.clearable}
      />
    );
  }
}
