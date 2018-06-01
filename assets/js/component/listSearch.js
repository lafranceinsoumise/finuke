import axios from '../lib/axios';
import React from 'react';
import Select from 'react-select';
import {Async} from 'react-select';
import 'react-select/dist/react-select.css';
import 'babel-polyfill';

import departementsData from 'CSVData/departements.csv';

const departements = departementsData.map(({
  CodeDept: code,
  NomDept,
  NomDeptEnr: name,
  TypNom,
  CodeRegion,
  ChefLieuDept,
  PopVotNuc,
  Intégration,
  PhyFile,
  NivDetail: details
}) => ({code: String(code), name, details}));

function findDepartement(number) {
  return departements.find(line => line.code.padStart(2, '0') == number.padStart(2, '0'));
}

class ListSearch extends React.Component {
  constructor(props) {
    super(props);
    this.state = {departement: '', commune: null, communesLoaded: false, person: null};
    this.departementChange = this.departementChange.bind(this);
    this.communeChange = this.communeChange.bind(this);
    this.searchPeople = this.searchPeople.bind(this);
    this.personChange = this.personChange.bind(this);
    this.opMode = this.props.mode === 'operator';
    this.departement = DEPARTEMENT;
    this.communes = COMMUNES;

    this.labels = {
      departementHelp: this.opMode ? 'Département d\'inscription de la personne': 'Recherchez votre département ci-dessus.',
      communePlaceholder: 'Commune d\'inscription',
      communePromptText: 'Tapez le nom de la commune d\'inscription',
      personPlaceholder : 'Prénom NOM',
      personPromptText: this.opMode ? 'Prénom et nom de la personne': 'Tapez votre prénom et votre nom',
      noListHint: this.opMode ?
        'Vous devez faire voter la personne avec un bulletin orange.'
        : (<span>Vous pouvez <a href={BASE_URL + '/vote'}>voter directement ici</a>.</span>),
      listErrorHint: this.opMode ?
        'faire voter la personne avec un bulletin orange'
        : (<a href={BASE_URL + '/vote'}>voter directement ici</a>),
    }
  }

  async componentDidMount() {
    if (!this.departement) return;

    let departementInfo = findDepartement(String(this.departement));

    this.setState({
      departement: this.departement,
      departementInfo : departementInfo,
      commune: null,
      communesLoaded: false,
    });

    this.communesChoice = (await axios(`/json/communes/${this.departement}?${__VERSION__}`)).data.map(c => ({value: c.code, label: c.name}))
    if (this.communes) {
      this.communesChoice = this.communesChoice.filter(c => this.communes.includes(c.value));
    }

    this.setState({
      communesLoaded: true
    });
  }

  async departementChange(event) {
    if (event.target.value.length > 4) {
      this.setState({
        displayZipHint: true
      });

      return;
    }

    let departementInfo = findDepartement(event.target.value);

    this.setState({
      displayZipHint: false,
      departement: event.target.value,
      departementInfo : departementInfo,
      commune: null,
      communesLoaded: false,
    });

    if (!departementInfo || departementInfo.details !== 'C') {
      return;
    }

    this.communesChoice = (await axios(`/json/communes/${event.target.value}?${__VERSION__}`)).data.map(c => ({value: c.code, label: c.name}));
    if (this.communes) {
      this.communesChoice = this.communesChoice.filter(c => this.communes.includes(c.value));
    }

    this.setState({communesLoaded: true});
  }

  communeChange(commune) {
    this.setState({commune});
  }

  async searchPeople(input) {
    return new Promise((resolve, reject) => {
      if (input.length < 4) return resolve({options: []});

      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout);
      }

      this.searchTimeout = setTimeout(async () => {
        let qs = this.state.commune ? `?commune=${this.state.commune.value}` : '';

        try {
          let options = (await axios(`/json/listes/${this.state.departementInfo.code}/${input}${qs}`)).data
          .map(p => ({value: p.id, label: `${p.first_names} ${p.last_name} - ${p.commune_name}`}));

          return resolve({options});
        } catch (e) {
          return reject(e);
        }
      }, 500);
    });
  }

  personChange(person) {
    this.setState({person, displayNoChoiceHint: false});
    if (this.props.onChange) {
      this.props.onChange(person);
    }
  }

  render() {
    return (
      <div>
        <div className="form-group">
          <input placeholder="Numéro de département d'inscription sur les listes électorales" type="text" className="text-center form-control input-lg" name="departement" value={this.state.departement} onChange={this.departementChange} autoComplete="off" disabled={this.departement}/>
        </div>
        {this.state.displayZipHint ?
        <div className="alert alert-warning">
          <p>
            Vous devez taper votre numéro de département (2 ou 3 chiffres) et non votre code postal&nbsp;!
          </p>
        </div> : ''}
        <p className="text-center">
          { this.state.departementInfo ? this.state.departementInfo.name : this.labels.departementHelp }
        </p>
        {this.state.departementInfo && this.state.departementInfo.details == 'D' ?
          <div className="alert alert-warning">
            Nous ne disposons malheureusement pas du détail par communes des listes électorales de ce département.
            Effectuez une recherche sur tout le département.
          </div>
          : <div className="form-group">
            <Select
              value={this.state.commune}
              onBlurResetsInput={false}
              onCloseResetsInput={false}
              onChange={this.communeChange}
              noResultsText={"Pas de résultats. N'oubliez pas le tirets !"}
              options={this.communesChoice}
              disabled={!this.state.communesLoaded}
              placeholder={this.labels.communePlaceholder}
              searchPromptText={this.labels.communePromptText}/>
          </div>
        }
        <div className="form-group">
          <Async
            name="person"
            onBlurResetsInput={false}
            onCloseResetsInput={false}
            inputProps={{autoComplete: 'full name'}}
            onBlur={() => this.setState({displayNoChoiceHint: true})}
            autoBlur={true}
            required={true}
            autoload={false}
            cache={false}
            filterOptions={(options, filter, currentValues) => {
              // Do no filtering, just return all options
              return options;
            }}
            value={this.state.person}
            disabled={!this.state.departementInfo || !this.state.departementInfo.details || (this.state.departementInfo.details == 'C' && !this.state.commune)}
            onChange={this.personChange}
            loadOptions={this.searchPeople}
            placeholder={this.labels.personPlaceholder}
            searchPromptText={this.labels.personPromptText}
            loadingPlaceholder="Chargement..." />
        </div>
        { this.state.displayNoChoiceHint ?
          <div className="alert alert-danger">
            <p>
              Vous devez cliquer sur un nom dans la liste déroulante. Les listes électorales sont celles de 2017
              transmises par la préfecture du département {this.state.departement}.
            </p>
            <p>
              Dans de très rares cas, il peut cependant subsister des erreurs. Si après avoir réessayé, vous ne trouvez
              toujours pas le nom dans la liste, merci de {this.labels.listErrorHint}.
            </p>
          </div>
        : '' }
        { this.state.departementInfo && !this.state.departementInfo.details ?
          <div className="alert alert-warning">
            Nous ne disposons malheureusement pas des listes électorales de ce département.
            {this.labels.noListHint}
          </div>
        : '' }
      </div>
    );
  }
}

export default ListSearch;
