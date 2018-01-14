import React, {Component} from 'react';
import PropTypes from 'prop-types';
import $ from 'jquery';

import {
    Button,
    Card,
    CardBody,
    CardTitle,
    Form,
    FormGroup,
    Input,
    Label,
    Table,
} from 'reactstrap';

import {
    actionRipTracks,
} from '../api.js'


class DiscInfo extends Component {

    constructor(props) {
        super(props);
        this.state = {
            checkAll: false,
            discName: this.props.discTitle,
        };
    }

    getTrackCheckboxes($formElement) {
        return $formElement
            .closest('fieldset')
            .find('input[name=selectTrack]');
    }

    // Toggle the checkbox on all tracks.
    toggleAllTracks(event) {
        let $target = $(event.target);
        this.state.checkAll = $target.prop('checked');
        this.getTrackCheckboxes(event.target)
            .prop('checked', this.state.checkAll);
    }

    // Command the server to rip certain tracks for this disc.
    ripTracks(event) {
        let ripTrackIds = this.getTrackCheckboxes(event.target)
            .find(':checked')
            .data('track-id');
        actionRipTracks(
            this.state.discName,
            this.props.driveId,
            ripTrackIds
        );
    }

    render(){
        return(
            <Form onSubmit={ this.handleSubmit }>
                <fieldset { ...(this.props.isRipping ? 'disabled' : '') } >
                    <FormGroup>
                        <Label for="discName">
                            Name
                        </Label>
                        <Input type="text"
                               value={ this.state.discName }
                               onChange={
                                   (event) => {
                                       this.setState({discName: event.target.value})
                                   }
                               }
                               />
                    </FormGroup>
                    <FormGroup name="discInfo">
                        <Table className="discInfo">
                            <thead>
                                <tr>
                                    <th>
                                        <Input type="checkbox"
                                               checked={this.state.checkAll}
                                               onChange={this.toggleAllTracks} />
                                    </th>
                                    <th>#</th>
                                    <th>Source</th>
                                    <th>Chptrs</th>
                                    <th>Size</th>
                                    <th>Streams</th>
                                    <th>Segments</th>
                                </tr>
                            </thead>
                            <tbody>
                            {
                                this.props.tracks.map(function(trackInfo) {
                                    return <tr>
                                        <td>
                                            <Input type="checkbox"
                                                   name="selectTrack"
                                                   data-track-id={ trackInfo.id }
                                                   { ...(trackInfo.isAutoSelected ? 'checked' : '') }
                                                />
                                        </td>
                                        <td>{ trackInfo.orderWeight }</td>
                                        <td>{ trackInfo.name }</td>
                                        <td>{ trackInfo.chapterCount }</td>
                                        <td>{ trackInfo.diskSize }</td>
                                        <td>{ trackInfo.streams.metadata }</td>
                                        <td>{ trackInfo.segments.map }</td>
                                    </tr>;
                                })
                            }
                            </tbody>
                        </Table>
                    </FormGroup>
                    <FormGroup>
                        <Button onClick={this.ripTracks} />
                    </FormGroup>
                </fieldset>
            </Form>
        );
    }
}

DiscInfo.propTypes = {
    isRipping: PropTypes.bool,
    metadata: PropTypes.shape({
        lngCode: PropTypes.string.isRequired,
        lngName: PropTypes.string.isRequired,
    }),
    name: PropTypes.string.isRequired,
    orderWeight: PropTypes.number.isRequired,
    sanitized: PropTypes.string,
    treeInfo: PropTypes.string.isRequired,
    driveId: PropTypes.string.isRequired,
    discType: PropTypes.string.isRequired,
    volumeName: PropTypes.string.isRequired,
    tracks: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.number.isRequired,
        isAutoSelected: PropTypes.bool,
        ripStatus: PropTypes.oneOf(['none', 'busy', 'fail', 'success']),
        chapterCount: PropTypes.number.isRequired,
        diskSize: PropTypes.string.isRequired,
        diskSizeBytes: PropTypes.number.isRequired,
        duration: PropTypes.string.isRequired,
        metadata: PropTypes.shape({
            lngCode: PropTypes.string.isRequired,
            lngName: PropTypes.string.isRequired,
        }),
        name: PropTypes.string.isRequired,
        orderWeight: PropTypes.number.isRequired,
        outputFileName: PropTypes.string.isRequired,
        segments: PropTypes.shape({
            count: PropTypes.number.isRequired,
            map: PropTypes.string.isRequired,
        }),
        sourceFileName: PropTypes.string.isRequired,
        treeInfo: PropTypes.string.isRequired,
        streams: PropTypes.shape({
            metadata: PropTypes.shape({
                audio: PropTypes.number.isRequired,
                subtitle: PropTypes.number.isRequired,
                video: PropTypes.number.isRequired,
            }),
            details: PropTypes.any,
        })
    })),
};

DiscInfo.defaultProps = {
    isRipping: false,
    tracks: [],
};

export default DiscInfo;
