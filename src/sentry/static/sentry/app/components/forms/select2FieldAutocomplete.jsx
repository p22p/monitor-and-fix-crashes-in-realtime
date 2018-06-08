import {debounce} from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';

import {t} from 'app/locale';
import {addErrorMessage} from 'app/actionCreators/indicator';
import {Client} from 'app/api';
import handleXhrErrorResponse from 'app/utils/handleXhrErrorResponse';
import Select2Field from './select2Field';
import SelectControl from './selectControl';

class Select2FieldAutocomplete extends Select2Field {
  static propTypes = {
    ...Select2Field.propTypes,
    // ajaxDelay: PropTypes.number,
    // minimumInputLength: PropTypes.number,
    // formatResult: PropTypes.func,
    // formatSelection: PropTypes.func,
    onResults: PropTypes.func,
    onQuery: PropTypes.func,
    url: PropTypes.string.isRequired,
    id: PropTypes.any,
  };

  static defaultProps = {
    ...Select2Field.defaultProps,
    placeholder: 'Start typing to search for an issue',
    onResults(data, name) {
      let results = data && data[name];

      return (results && results.map(({id, text}) => ({value: id, label: text}))) || [];
    },
    onQuery(query, name) {
      return {autocomplete_query: query, autocomplete_field: name};
    },
    minimumInputLength: null,
  };

  constructor(props) {
    super(props);
    this.api = new Client();
    this.state = {
      query: '',
    };
  }

  componentWillUnmount() {
    super.componentWillUnmount();
    if (!this.api) return;
    this.api.clear();
    this.api = null;
  }

  doQuery = debounce(cb => {
    let {url, onQuery, name} = this.props;
    let {query} = this.state;

    if (!this.api) return null;

    return this.api
      .requestPromise(url, {
        query: typeof onQuery === 'function' ? onQuery(query, name) : query,
      })
      .then(data => cb(null, data), err => cb(err));
  }, 250);

  handleLoadOptions = () => {
    return new Promise((resolve, reject) => {
      this.doQuery((err, result) => {
        console.log(result);
        if (err) {
          reject(err);
        } else {
          resolve(result);
        }
      });
    }).then(
      resp => {
        let {name, onResults} = this.props;
        return {
          options: typeof onResults === 'function' ? onResults(resp, name) : resp,
        };
      },
      err => {
        addErrorMessage(t('There was a problem with the request.'));
        handleXhrErrorResponse('SelectAutocomplete failed')(err);
      }
    );
  };

  handleInputChange = query => {
    this.setState({query});
  };

  getField() {
    return (
      <SelectControl
        value={this.state.value}
        loadOptions={this.handleLoadOptions}
        defaultOptions
        onInputChange={this.handleInputChange}
        onClear={this.handleClear}
        async
        cache={false}
        {...this.props}
        id={this.getId()}
      />
    );
  }
}

function forwardRef(props, ref) {
  return <Select2FieldAutocomplete {...props} forwardedRef={ref} />;
}
forwardRef.displayName = 'forwardRef(Select2FieldAutocomplete)';

export default React.forwardRef(forwardRef);
